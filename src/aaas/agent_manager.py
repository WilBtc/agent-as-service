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

from claude_agent_sdk import ClaudeSDKClient, query
from claude_agent_sdk.models import ClaudeAgentOptions, AssistantMessage, UserMessage

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

            # Prepare environment
            env = os.environ.copy()
            if settings.claude_api_key:
                env["ANTHROPIC_API_KEY"] = settings.claude_api_key

            # Add custom environment variables
            if self.config.environment:
                env.update(self.config.environment)

            # Build Claude Agent Options
            agent_options = ClaudeAgentOptions(
                cwd=self.working_dir,
                system_prompt=agent_type_config.get("system_prompt"),
                allowed_tools=agent_type_config.get("allowed_tools"),
                permission_mode=agent_type_config.get("permission_mode").value,
                max_turns=self.config.max_turns,
                model=self.config.model or settings.claude_model,
            )

            # Initialize Claude SDK Client
            self.client = ClaudeSDKClient(
                api_key=settings.claude_api_key,
                options=agent_options,
            )

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

                # Cleanup client resources
                await self.client.close()
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

            # Create user message
            user_message = UserMessage(content=message)

            # Add context if provided
            if context:
                # You can optionally prepend context to the message
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                user_message = UserMessage(content=f"Context:\n{context_str}\n\nMessage: {message}")

            # Send message and get response
            response_messages = []
            async for response_message in self.client.send_message(user_message):
                response_messages.append(response_message)
                logger.debug(f"Agent {self.agent_id} response chunk: {response_message}")

            # Extract text content from response messages
            response_text = self._extract_text_from_messages(response_messages)

            self.messages_count += 1
            self._conversation_history.append({
                "user": message,
                "assistant": response_text,
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info(f"Agent {self.agent_id} responded successfully")
            return response_text

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from agent {self.agent_id}")
            raise
        except Exception as e:
            logger.error(f"Error sending message to agent {self.agent_id}: {e}", exc_info=True)
            raise

    def _extract_text_from_messages(self, messages: List[Any]) -> str:
        """Extract text content from response messages"""
        text_parts = []
        for message in messages:
            if isinstance(message, AssistantMessage):
                # Extract text from assistant message
                if hasattr(message, 'content'):
                    if isinstance(message.content, str):
                        text_parts.append(message.content)
                    elif isinstance(message.content, list):
                        for content_block in message.content:
                            if hasattr(content_block, 'text'):
                                text_parts.append(content_block.text)
                            elif isinstance(content_block, dict) and 'text' in content_block:
                                text_parts.append(content_block['text'])
            elif isinstance(message, dict) and 'content' in message:
                text_parts.append(str(message['content']))

        return "\n".join(text_parts) if text_parts else "No response received"

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

            # Use SDK's query function for simple one-off queries
            response_text = ""
            async for message in query(prompt=prompt):
                if hasattr(message, 'content'):
                    response_text += str(message.content)

            return response_text if response_text else "No response received"

        except Exception as e:
            logger.error(f"Error in quick query: {e}", exc_info=True)
            raise


# Global agent manager instance
agent_manager = AgentManager()


def get_agent_manager() -> AgentManager:
    """Get the global agent manager"""
    return agent_manager
