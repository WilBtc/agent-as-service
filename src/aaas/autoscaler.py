"""
Intelligent auto-scaling for agent management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from collections import deque

from .models import AgentConfig, AgentType, AgentStatus
from .metrics import track_autoscale_event, autoscale_agents_gauge

logger = logging.getLogger(__name__)


class AgentAutoscaler:
    """Intelligent agent auto-scaling based on demand"""

    def __init__(self, manager, settings):
        self.manager = manager
        self.settings = settings
        self.metrics_window = timedelta(minutes=5)
        self.request_history = deque(maxlen=1000)
        self.scale_cooldown = timedelta(minutes=2)
        self.last_scale_up = None
        self.last_scale_down = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Auto-scaling configuration
        self.min_agents = getattr(settings, 'min_agents', 1)
        self.max_agents = settings.max_agents
        self.scale_up_threshold = getattr(settings, 'scale_up_threshold', 0.8)
        self.scale_down_threshold = getattr(settings, 'scale_down_threshold', 0.3)
        self.enable_auto_recovery = getattr(settings, 'enable_auto_recovery', True)

    async def start(self):
        """Start autoscaling loop"""
        if self._running:
            logger.warning("Autoscaler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._autoscale_loop())
        logger.info(
            f"Autoscaler started: min={self.min_agents}, max={self.max_agents}, "
            f"scale_up={self.scale_up_threshold}, scale_down={self.scale_down_threshold}"
        )

    async def stop(self):
        """Stop autoscaling"""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Autoscaler stopped")

    async def _autoscale_loop(self):
        """Main autoscaling loop"""
        while self._running:
            try:
                await self._autoscale_check()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autoscaling error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Back off on error

    async def _autoscale_check(self):
        """Check if scaling is needed"""
        try:
            agents = await self.manager.list_agents()
            current_count = len(agents)

            # Count agents by status
            status_counts = self._count_agents_by_status(agents)
            running_count = status_counts.get('running', 0)
            idle_count = status_counts.get('idle', 0)
            error_count = status_counts.get('error', 0)

            # Calculate demand metrics
            recent_request_rate = self._get_recent_request_rate()
            utilization = running_count / self.max_agents if self.max_agents > 0 else 0
            idle_utilization = idle_count / max(current_count, 1)

            logger.debug(
                f"Autoscaler check: total={current_count}, running={running_count}, "
                f"idle={idle_count}, error={error_count}, utilization={utilization:.2f}, "
                f"request_rate={recent_request_rate:.2f}/min"
            )

            # Check for unhealthy agents needing recovery
            if self.enable_auto_recovery and error_count > 0:
                await self._recover_failed_agents(agents)

            # Scale up decision
            if self._should_scale_up(utilization, current_count, recent_request_rate, running_count):
                scale_up_count = self._calculate_scale_up_count(current_count, running_count)
                await self._scale_up(scale_up_count)

            # Scale down decision
            elif self._should_scale_down(utilization, idle_utilization, current_count, recent_request_rate):
                scale_down_count = self._calculate_scale_down_count(idle_count)
                await self._scale_down(scale_down_count)

            # Update metrics
            autoscale_agents_gauge.set(current_count)

        except Exception as e:
            logger.error(f"Error in autoscale check: {e}", exc_info=True)

    def _should_scale_up(
        self,
        utilization: float,
        current_count: int,
        recent_request_rate: float,
        running_count: int
    ) -> bool:
        """Determine if scale up is needed"""
        # Don't scale up if we're at max
        if current_count >= self.max_agents:
            return False

        # Check cooldown period
        if self.last_scale_up and (datetime.utcnow() - self.last_scale_up) < self.scale_cooldown:
            return False

        # Scale up if utilization is high
        if utilization > self.scale_up_threshold:
            return True

        # Scale up if request rate is high relative to running agents
        if running_count > 0 and recent_request_rate > running_count * 0.8:
            return True

        return False

    def _should_scale_down(
        self,
        utilization: float,
        idle_utilization: float,
        current_count: int,
        recent_request_rate: float
    ) -> bool:
        """Determine if scale down is needed"""
        # Don't scale down if we're at minimum
        if current_count <= self.min_agents:
            return False

        # Check cooldown period
        if self.last_scale_down and (datetime.utcnow() - self.last_scale_down) < self.scale_cooldown:
            return False

        # Scale down if utilization is low
        if utilization < self.scale_down_threshold and idle_utilization > 0.5:
            return True

        # Scale down if request rate is very low
        if recent_request_rate < current_count * 0.2:
            return True

        return False

    def _calculate_scale_up_count(self, current_count: int, running_count: int) -> int:
        """Calculate how many agents to add"""
        # Scale by 50% of current count, or at least 2
        scale_count = max(int(current_count * 0.5), 2)

        # Don't exceed max agents
        scale_count = min(scale_count, self.max_agents - current_count)

        return max(scale_count, 1)

    def _calculate_scale_down_count(self, idle_count: int) -> int:
        """Calculate how many agents to remove"""
        # Remove 30% of idle agents, or at least 1
        scale_count = max(int(idle_count * 0.3), 1)

        return min(scale_count, idle_count)

    async def _scale_up(self, count: int):
        """Scale up by creating idle agents"""
        logger.info(f"Scaling up: creating {count} agents")
        track_autoscale_event('up', f'creating_{count}_agents')

        created_count = 0
        for i in range(count):
            try:
                # Create general-purpose agent
                config = AgentConfig(agent_type=AgentType.GENERAL)
                agent_id = await self.manager.create_agent(config, auto_start=False)
                created_count += 1
                logger.debug(f"Created idle agent {agent_id} ({i+1}/{count})")
            except Exception as e:
                logger.error(f"Failed to create agent during scale-up: {e}")

        self.last_scale_up = datetime.utcnow()
        logger.info(f"Scale up completed: created {created_count}/{count} agents")

    async def _scale_down(self, count: int):
        """Scale down by removing idle agents"""
        logger.info(f"Scaling down: removing up to {count} idle agents")
        track_autoscale_event('down', f'removing_{count}_agents')

        agents = await self.manager.list_agents()

        # Find idle agents (stopped or running with no messages)
        idle_agents = []
        for agent_id, agent_info in agents.items():
            agent = await self.manager.get_agent(agent_id)
            if not agent:
                continue

            if (agent.status == AgentStatus.STOPPED or
                agent.status == AgentStatus.IDLE or
                (agent.status == AgentStatus.RUNNING and agent.messages_count == 0)):
                idle_agents.append((agent_id, agent))

        # Sort by creation time (oldest first)
        idle_agents.sort(key=lambda x: x[1].created_at)

        # Remove oldest idle agents
        removed_count = 0
        for agent_id, agent in idle_agents[:count]:
            try:
                await self.manager.delete_agent(agent_id)
                removed_count += 1
                logger.debug(f"Removed idle agent {agent_id}")
            except Exception as e:
                logger.error(f"Failed to remove agent {agent_id}: {e}")

        self.last_scale_down = datetime.utcnow()
        logger.info(f"Scale down completed: removed {removed_count}/{count} agents")

    async def _recover_failed_agents(self, agents: Dict):
        """Attempt to recover failed agents"""
        error_agents = [
            (agent_id, await self.manager.get_agent(agent_id))
            for agent_id, agent_info in agents.items()
            if agent_info.status == AgentStatus.ERROR
        ]

        for agent_id, agent in error_agents:
            if not agent:
                continue

            try:
                logger.info(f"Attempting to recover failed agent {agent_id}")
                success = await agent.recover()

                if success:
                    logger.info(f"Successfully recovered agent {agent_id}")
                else:
                    logger.warning(f"Failed to recover agent {agent_id}")
            except Exception as e:
                logger.error(f"Error recovering agent {agent_id}: {e}")

    def track_request(self):
        """Track a request for autoscaling decisions"""
        now = datetime.utcnow()
        self.request_history.append(now)

    def _get_recent_request_rate(self) -> float:
        """Get request rate per minute over the metrics window"""
        if not self.request_history:
            return 0.0

        now = datetime.utcnow()
        cutoff = now - self.metrics_window

        # Count recent requests
        recent_requests = sum(1 for ts in self.request_history if ts > cutoff)

        # Calculate rate per minute
        window_minutes = self.metrics_window.total_seconds() / 60
        return recent_requests / window_minutes if window_minutes > 0 else 0.0

    def _count_agents_by_status(self, agents: Dict) -> Dict[str, int]:
        """Count agents grouped by status"""
        counts = {}
        for agent_info in agents.values():
            status = agent_info.status.value if hasattr(agent_info.status, 'value') else str(agent_info.status)
            counts[status] = counts.get(status, 0) + 1
        return counts

    def get_stats(self) -> dict:
        """Get current autoscaler statistics"""
        return {
            'enabled': self._running,
            'min_agents': self.min_agents,
            'max_agents': self.max_agents,
            'scale_up_threshold': self.scale_up_threshold,
            'scale_down_threshold': self.scale_down_threshold,
            'recent_request_rate': self._get_recent_request_rate(),
            'last_scale_up': self.last_scale_up.isoformat() if self.last_scale_up else None,
            'last_scale_down': self.last_scale_down.isoformat() if self.last_scale_down else None,
            'request_history_size': len(self.request_history)
        }
