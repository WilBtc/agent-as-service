"""
Agent Manager - Manages Claude Code subprocess instances
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import signal

from .config import settings
from .models import AgentConfig, AgentInfo, AgentStatus


logger = logging.getLogger(__name__)


class ClaudeCodeAgent:
    """Manages a single Claude Code subprocess instance"""

    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config
        self.status = AgentStatus.STOPPED
        self.created_at = datetime.utcnow()
        self.process: Optional[asyncio.subprocess.Process] = None
        self.working_dir = config.working_directory or os.path.join(
            settings.default_working_dir, agent_id
        )
        self.messages_count = 0
        self._stdin_lock = asyncio.Lock()
        self._output_buffer = []
        self._reader_task: Optional[asyncio.Task] = None

    async def start(self) -> bool:
        """Start the Claude Code subprocess"""
        try:
            logger.info(f"Starting agent {self.agent_id} with config: {self.config}")
            self.status = AgentStatus.STARTING

            # Create working directory
            Path(self.working_dir).mkdir(parents=True, exist_ok=True)

            # Prepare environment
            env = os.environ.copy()
            if settings.claude_api_key:
                env["ANTHROPIC_API_KEY"] = settings.claude_api_key

            # Add custom environment variables
            if self.config.environment:
                env.update(self.config.environment)

            # Build command
            cmd = [settings.claude_code_path]

            # Start Claude Code process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.working_dir,
            )

            # Start output reader task
            self._reader_task = asyncio.create_task(self._read_output())

            self.status = AgentStatus.RUNNING
            logger.info(f"Agent {self.agent_id} started with PID {self.process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self.status = AgentStatus.ERROR
            return False

    async def stop(self) -> bool:
        """Stop the Claude Code subprocess"""
        try:
            if self.process:
                logger.info(f"Stopping agent {self.agent_id}")

                # Cancel reader task
                if self._reader_task:
                    self._reader_task.cancel()
                    try:
                        await self._reader_task
                    except asyncio.CancelledError:
                        pass

                # Terminate process gracefully
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Agent {self.agent_id} didn't terminate, killing it")
                    self.process.kill()
                    await self.process.wait()

                self.status = AgentStatus.STOPPED
                logger.info(f"Agent {self.agent_id} stopped")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            return False

    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send a message to the Claude Code agent"""
        if not self.process or self.status != AgentStatus.RUNNING:
            raise RuntimeError(f"Agent {self.agent_id} is not running")

        try:
            async with self._stdin_lock:
                # Clear output buffer before sending
                self._output_buffer.clear()

                # Send message to Claude Code
                self.process.stdin.write(f"{message}\n".encode())
                await self.process.stdin.drain()

                # Wait for response (with timeout)
                response = await asyncio.wait_for(
                    self._wait_for_response(), timeout=settings.agent_timeout
                )

                self.messages_count += 1
                return response

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from agent {self.agent_id}")
            raise
        except Exception as e:
            logger.error(f"Error sending message to agent {self.agent_id}: {e}")
            raise

    async def _read_output(self):
        """Continuously read output from the subprocess"""
        try:
            while True:
                if not self.process or not self.process.stdout:
                    break

                line = await self.process.stdout.readline()
                if not line:
                    break

                decoded_line = line.decode().strip()
                if decoded_line:
                    self._output_buffer.append(decoded_line)
                    logger.debug(f"Agent {self.agent_id} output: {decoded_line}")

        except Exception as e:
            logger.error(f"Error reading output from agent {self.agent_id}: {e}")

    async def _wait_for_response(self) -> str:
        """Wait for a complete response from the agent"""
        # Simple implementation - wait for output to stabilize
        # In a real implementation, you'd want a more sophisticated protocol
        response_lines = []
        no_output_count = 0
        max_no_output = 5  # Wait for 5 iterations without output

        while no_output_count < max_no_output:
            await asyncio.sleep(0.1)

            if self._output_buffer:
                response_lines.extend(self._output_buffer)
                self._output_buffer.clear()
                no_output_count = 0
            else:
                no_output_count += 1

        return "\n".join(response_lines) if response_lines else "No response received"

    def get_info(self) -> AgentInfo:
        """Get agent information"""
        return AgentInfo(
            id=self.agent_id,
            status=self.status,
            config=self.config,
            created_at=self.created_at,
            endpoint=f"/api/v1/agents/{self.agent_id}",
            pid=self.process.pid if self.process else None,
            messages_count=self.messages_count,
        )


class AgentManager:
    """Manages multiple Claude Code agent instances"""

    def __init__(self):
        self.agents: Dict[str, ClaudeCodeAgent] = {}
        self._lock = asyncio.Lock()

    async def create_agent(self, config: AgentConfig, auto_start: bool = True) -> str:
        """Create a new agent instance"""
        async with self._lock:
            if len(self.agents) >= settings.max_agents:
                raise ValueError(f"Maximum number of agents ({settings.max_agents}) reached")

            agent_id = str(uuid.uuid4())
            agent = ClaudeCodeAgent(agent_id, config)
            self.agents[agent_id] = agent

            if auto_start:
                await agent.start()

            logger.info(f"Created agent {agent_id}")
            return agent_id

    async def get_agent(self, agent_id: str) -> Optional[ClaudeCodeAgent]:
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
            logger.info(f"Deleted agent {agent_id}")
            return True

    async def shutdown_all(self):
        """Shutdown all agents"""
        logger.info("Shutting down all agents")
        tasks = [agent.stop() for agent in self.agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.agents.clear()


# Global agent manager instance
agent_manager = AgentManager()


def get_agent_manager() -> AgentManager:
    """Get the global agent manager"""
    return agent_manager
