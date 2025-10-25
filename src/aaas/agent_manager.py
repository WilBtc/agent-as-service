"""
Agent Manager - Manages Claude Agent SDK instances
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
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


logger = logging.getLogger(__name__)


class ClaudeAgent:
    """Manages a single Claude Agent SDK instance"""

    def __init__(self, agent_id: str, config: AgentConfig):
        self.agent_id = agent_id
        self.config = config
        self.status = AgentStatus.STOPPED
        self.created_at = datetime.utcnow()
        self.client: Optional[ClaudeSDKClient] = None
        self.working_dir = config.working_directory or os.path.join(
            settings.default_working_dir, agent_id
        )
        self.messages_count = 0
        self._conversation_history: List[Any] = []
        self._client_task: Optional[asyncio.Task] = None

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
            logger.info(f"Agent {self.agent_id} started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}", exc_info=True)
            self.status = AgentStatus.ERROR
            return False

    async def stop(self) -> bool:
        """Stop the Claude Agent"""
        try:
            if self.client:
                logger.info(f"Stopping agent {self.agent_id}")

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
                logger.info(f"Agent {self.agent_id} stopped")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to stop agent {self.agent_id}: {e}")
            return False

    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send a message to the Claude Agent"""
        if not self.client or self.status != AgentStatus.RUNNING:
            raise RuntimeError(f"Agent {self.agent_id} is not running")

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
            self._conversation_history.append({
                "user": message,
                "assistant": response_text,
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info(f"Agent {self.agent_id} responded successfully")
            return response_text if response_text else "No response received"

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from agent {self.agent_id}")
            raise
        except Exception as e:
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


class AgentManager:
    """Manages multiple Claude Agent instances"""

    def __init__(self):
        self.agents: Dict[str, ClaudeAgent] = {}
        self._lock = asyncio.Lock()

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
            logger.info(f"Deleted agent {agent_id}")
            return True

    async def shutdown_all(self):
        """Shutdown all agents"""
        logger.info("Shutting down all agents")
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
