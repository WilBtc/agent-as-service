"""
Agent Manager - Manages Claude Agent SDK instances
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List, Any

# FIXED: Correct imports for Claude Agent SDK
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query

from .config import settings
from .models import (
    AgentConfig,
    AgentInfo,
    AgentStatus,
    AgentType,
    PermissionMode,
    get_agent_config_for_type,
)
from .metrics import (
    track_agent_creation,
    track_agent_start,
    track_agent_stop,
    track_agent_deletion,
    track_agent_error,
    track_agent_recovery,
    track_message,
    update_active_agents,
)


logger = logging.getLogger(__name__)


class ClaudeAgent:
    """Manages a single Claude Agent SDK instance"""

    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config
        self.status = AgentStatus.STOPPED
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.client: Optional[ClaudeSDKClient] = None
        self.working_dir = config.working_directory or os.path.join(
            settings.default_working_dir, agent_id
        )
        self.messages_count = 0
        self._conversation_history: List[Any] = []
        self._client_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._idle_monitor_task: Optional[asyncio.Task] = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = settings.max_recovery_attempts

    async def start(self) -> bool:
        """Start the Claude Agent"""
        try:
            logger.info(f"Starting agent {self.agent_id} with config: {self.config}")
            self.status = AgentStatus.STARTING

            # Create working directory
            Path(self.working_dir).mkdir(parents=True, exist_ok=True)

            # Get agent type configuration
            agent_type_config = get_agent_config_for_type(
                self.config.agent_type, self.config
            )

            # FIXED: Set API key via environment variable (SDK requirement)
            if settings.claude_api_key:
                os.environ["ANTHROPIC_API_KEY"] = settings.claude_api_key

            # Add custom environment variables
            if self.config.environment:
                for key, value in self.config.environment.items():
                    os.environ[key] = value

            # FIXED: Convert permission mode enum to string
            permission_mode_str = agent_type_config.get("permission_mode")
            if isinstance(permission_mode_str, PermissionMode):
                permission_mode_str = permission_mode_str.value

            # FIXED: Build Claude Agent Options (removed model parameter)
            agent_options = ClaudeAgentOptions(
                cwd=self.working_dir,
                system_prompt=agent_type_config.get("system_prompt"),
                allowed_tools=agent_type_config.get("allowed_tools"),
                permission_mode=permission_mode_str,
                max_turns=self.config.max_turns,
            )

            # FIXED: Initialize Claude SDK Client without api_key parameter
            # Using context manager pattern as recommended
            self.client = ClaudeSDKClient(options=agent_options)

            # Note: Client initialization happens, but we enter context when sending messages

            self.status = AgentStatus.RUNNING
            self.last_activity = datetime.now(timezone.utc)

            # Track metrics
            track_agent_start(str(self.config.agent_type))

            # Start health monitoring if enabled
            if settings.enable_health_monitoring:
                self._health_check_task = asyncio.create_task(self._health_check_loop())

            # Start idle monitoring if enabled
            if settings.enable_idle_shutdown:
                self._idle_monitor_task = asyncio.create_task(self._idle_monitor_loop())

            logger.info(f"Agent {self.agent_id} started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}", exc_info=True)
            self.status = AgentStatus.ERROR
            track_agent_error("start_failure", str(self.config.agent_type))
            return False

    async def stop(self) -> bool:
        """Stop the Claude Agent"""
        try:
            if self.client:
                logger.info(f"Stopping agent {self.agent_id}")

                # Cancel monitoring tasks
                if self._health_check_task and not self._health_check_task.done():
                    self._health_check_task.cancel()
                    try:
                        await self._health_check_task
                    except asyncio.CancelledError:
                        pass

                if self._idle_monitor_task and not self._idle_monitor_task.done():
                    self._idle_monitor_task.cancel()
                    try:
                        await self._idle_monitor_task
                    except asyncio.CancelledError:
                        pass

                # Cancel any ongoing tasks
                if self._client_task and not self._client_task.done():
                    self._client_task.cancel()
                    try:
                        await self._client_task
                    except asyncio.CancelledError:
                        pass

                # Cleanup client resources
                self.client = None

                self.status = AgentStatus.STOPPED
                track_agent_stop()
                logger.info(f"Agent {self.agent_id} stopped")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            track_agent_error("stop_failure", str(self.config.agent_type))
            return False

    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send a message to the Claude Agent"""
        if not self.client or self.status != AgentStatus.RUNNING:
            raise RuntimeError(f"Agent {self.agent_id} is not running")

        start_time = datetime.now(timezone.utc)

        try:
            logger.info(f"Sending message to agent {self.agent_id}: {message[:100]}...")

            # Prepend context if provided
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                full_message = f"Context:\n{context_str}\n\nMessage: {message}"
            else:
                full_message = message

            # FIXED: Use correct SDK API pattern
            # Use context manager for each interaction
            response_text = ""

            async with self.client as client:
                # Send query
                await client.query(full_message)

                # Receive response
                async for response_message in client.receive_response():
                    # Extract text from response
                    text = self._extract_text_from_message(response_message)
                    if text:
                        response_text += text
                        logger.debug(f"Agent {self.agent_id} response chunk: {text[:100]}...")

            self.messages_count += 1
            self.last_activity = datetime.now(timezone.utc)
            self._conversation_history.append({
                "user": message,
                "assistant": response_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Track metrics
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            track_message(str(self.config.agent_type), "success", duration)

            logger.info(f"Agent {self.agent_id} responded successfully")
            return response_text if response_text else "No response received"

        except asyncio.TimeoutError:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            track_message(str(self.config.agent_type), "timeout", duration)
            track_agent_error("message_timeout", str(self.config.agent_type))
            logger.error(f"Timeout waiting for response from agent {self.agent_id}")
            raise
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            track_message(str(self.config.agent_type), "error", duration)
            track_agent_error("message_error", str(self.config.agent_type))
            logger.error(f"Error sending message to agent {self.agent_id}: {e}", exc_info=True)
            raise

    def _extract_text_from_message(self, message: Any) -> str:
        """Extract text content from a response message"""
        try:
            # Handle different message types
            if hasattr(message, 'content'):
                content = message.content

                # String content
                if isinstance(content, str):
                    return content

                # List of content blocks
                elif isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if hasattr(block, 'text'):
                            text_parts.append(block.text)
                        elif isinstance(block, dict) and 'text' in block:
                            text_parts.append(block['text'])
                        elif hasattr(block, 'type') and block.type == 'text':
                            if hasattr(block, 'text'):
                                text_parts.append(block.text)

                    if text_parts:
                        return "\n".join(text_parts)

            # Fallback to string representation
            return str(message)

        except Exception as e:
            logger.warning(f"Error extracting text from message: {e}")
            return str(message)

    def get_info(self) -> AgentInfo:
        """Get agent information"""
        return AgentInfo(
            id=self.agent_id,
            status=self.status,
            config=self.config,
            created_at=self.created_at,
            endpoint=f"/api/v1/agents/{self.agent_id}",
            pid=None,  # SDK doesn't expose process ID
            messages_count=self.messages_count,
        )

    async def _health_check_loop(self):
        """Periodic health check for the agent"""
        logger.info(f"Starting health check loop for agent {self.agent_id}")

        while self.status == AgentStatus.RUNNING:
            try:
                await asyncio.sleep(settings.health_check_interval)

                # Check if agent is responsive
                is_healthy = await self._check_health()

                if not is_healthy and self.status == AgentStatus.RUNNING:
                    logger.warning(f"Agent {self.agent_id} failed health check")
                    self.status = AgentStatus.ERROR
                    track_agent_error("health_check_failed", str(self.config.agent_type))

                    # Attempt recovery if enabled
                    if settings.enable_auto_recovery:
                        await self.recover()

            except asyncio.CancelledError:
                logger.info(f"Health check loop cancelled for agent {self.agent_id}")
                break
            except Exception as e:
                logger.error(f"Error in health check loop for agent {self.agent_id}: {e}")

    async def _check_health(self) -> bool:
        """Check if agent is healthy"""
        try:
            # Basic health check - verify client exists and status is correct
            if not self.client:
                return False

            if self.status != AgentStatus.RUNNING:
                return False

            # Check if agent is not stuck (has had recent activity or hasn't timed out)
            idle_time = (datetime.now(timezone.utc) - self.last_activity).total_seconds()
            if idle_time > settings.agent_timeout:
                logger.warning(f"Agent {self.agent_id} exceeded timeout ({idle_time}s > {settings.agent_timeout}s)")
                return False

            return True

        except Exception as e:
            logger.error(f"Health check failed for agent {self.agent_id}: {e}")
            return False

    async def _idle_monitor_loop(self):
        """Monitor agent for idle timeout"""
        logger.info(f"Starting idle monitor for agent {self.agent_id}")

        while self.status == AgentStatus.RUNNING:
            try:
                await asyncio.sleep(60)  # Check every minute

                idle_time = (datetime.now(timezone.utc) - self.last_activity).total_seconds()

                if idle_time > settings.agent_idle_timeout:
                    logger.info(f"Agent {self.agent_id} idle timeout ({idle_time}s), shutting down")
                    self.status = AgentStatus.IDLE
                    await self.stop()
                    break

            except asyncio.CancelledError:
                logger.info(f"Idle monitor cancelled for agent {self.agent_id}")
                break
            except Exception as e:
                logger.error(f"Error in idle monitor for agent {self.agent_id}: {e}")

    async def recover(self) -> bool:
        """Attempt to recover a failed agent"""
        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.error(f"Agent {self.agent_id} exceeded max recovery attempts ({self.max_recovery_attempts})")
            track_agent_recovery(str(self.config.agent_type), False)
            return False

        self.recovery_attempts += 1
        self.status = AgentStatus.RECOVERING

        logger.info(f"Attempting recovery for agent {self.agent_id} (attempt {self.recovery_attempts}/{self.max_recovery_attempts})")

        try:
            # Stop the agent
            await self.stop()

            # Wait with exponential backoff
            backoff_time = settings.recovery_backoff_seconds * (2 ** (self.recovery_attempts - 1))
            logger.info(f"Waiting {backoff_time}s before restart...")
            await asyncio.sleep(backoff_time)

            # Restart the agent
            success = await self.start()

            if success:
                logger.info(f"Successfully recovered agent {self.agent_id}")
                self.recovery_attempts = 0  # Reset counter on success
                track_agent_recovery(str(self.config.agent_type), True)
                return True
            else:
                logger.warning(f"Failed to recover agent {self.agent_id}")
                track_agent_recovery(str(self.config.agent_type), False)
                return False

        except Exception as e:
            logger.error(f"Error during recovery of agent {self.agent_id}: {e}", exc_info=True)
            self.status = AgentStatus.ERROR
            track_agent_recovery(str(self.config.agent_type), False)
            return False


class AgentManager:
    """Manages multiple Claude Agent instances"""

    def __init__(self):
        self.agents: Dict[str, ClaudeAgent] = {}
        self._lock = asyncio.Lock()
        self.autoscaler = None

        # Initialize autoscaler if enabled
        if settings.enable_autoscaling:
            from .autoscaler import AgentAutoscaler
            self.autoscaler = AgentAutoscaler(self, settings)

    async def create_agent(self, config: AgentConfig, auto_start: bool = True) -> str:
        """Create a new agent instance"""
        async with self._lock:
            if len(self.agents) >= settings.max_agents:
                raise ValueError(f"Maximum number of agents ({settings.max_agents}) reached")

            # Handle backward compatibility with template field
            if config.template and not config.agent_type:
                # Try to map template to agent type
                template_lower = config.template.lower()
                if "research" in template_lower:
                    config.agent_type = AgentType.RESEARCH
                elif "code" in template_lower or "developer" in template_lower:
                    config.agent_type = AgentType.CODE
                elif "finance" in template_lower:
                    config.agent_type = AgentType.FINANCE
                elif "support" in template_lower or "customer" in template_lower:
                    config.agent_type = AgentType.CUSTOMER_SUPPORT
                elif "assistant" in template_lower:
                    config.agent_type = AgentType.PERSONAL_ASSISTANT
                elif "data" in template_lower or "analysis" in template_lower:
                    config.agent_type = AgentType.DATA_ANALYSIS
                else:
                    config.agent_type = AgentType.GENERAL

            agent_id = str(uuid.uuid4())
            agent = ClaudeAgent(agent_id, config)
            self.agents[agent_id] = agent

            if auto_start:
                await agent.start()

            # Track metrics
            track_agent_creation(str(config.agent_type), auto_start)

            # Track with autoscaler
            if self.autoscaler:
                self.autoscaler.track_request()

            logger.info(f"Created agent {agent_id} of type {config.agent_type}")
            return agent_id

    async def get_agent(self, agent_id: str) -> Optional[ClaudeAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    async def list_agents(self) -> Dict[str, AgentInfo]:
        """List all agents"""
        return {agent_id: agent.get_info() for agent_id, agent in self.agents.items()}

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        async with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return False

            # Stop the agent if running
            if agent.status == AgentStatus.RUNNING:
                await agent.stop()

            del self.agents[agent_id]

            # Track metrics
            track_agent_deletion("user_requested")

            logger.info(f"Deleted agent {agent_id}")
            return True

    async def shutdown_all(self):
        """Shutdown all agents"""
        logger.info("Shutting down all agents")

        # Stop autoscaler first
        if self.autoscaler:
            await self.autoscaler.stop()

        # Stop all agents
        tasks = [agent.stop() for agent in self.agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.agents.clear()

    async def query_agent(self, prompt: str, agent_type: AgentType = AgentType.GENERAL) -> str:
        """Quick query using the SDK's query function - creates a temporary agent"""
        try:
            logger.info(f"Quick query with agent type {agent_type}: {prompt[:100]}...")

            # Get agent type configuration
            agent_type_config = get_agent_config_for_type(agent_type)

            # Set API key via environment
            if settings.claude_api_key:
                os.environ["ANTHROPIC_API_KEY"] = settings.claude_api_key

            # Use SDK's query function for simple one-off queries
            response_text = ""
            async for message in query(prompt=prompt):
                text = str(message)
                response_text += text

            return response_text if response_text else "No response received"

        except Exception as e:
            logger.error(f"Error in quick query: {e}", exc_info=True)
            raise


# Global agent manager instance
agent_manager = AgentManager()


def get_agent_manager() -> AgentManager:
    """Get the global agent manager"""
    return agent_manager
