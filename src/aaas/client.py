"""
Python client for Agent as a Service
"""

import httpx
from typing import Dict, Optional, Any
from datetime import datetime

from .models import AgentConfig, AgentInfo, AgentResponse, CreateAgentRequest, AgentType


class AgentClient:
    """Client for interacting with AaaS API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize the AaaS client

        Args:
            api_key: API key for authentication
            base_url: Base URL of the AaaS server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api/v1"
        self.timeout = timeout

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        self.client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)

    def deploy_agent(
        self,
        agent_type: Optional[AgentType] = None,
        template: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        auto_start: bool = True,
    ) -> "DeployedAgent":
        """
        Deploy a new agent

        Args:
            agent_type: Agent type (AgentType enum) - preferred method
            template: Agent template or type (deprecated, use agent_type)
            config: Additional configuration options
            auto_start: Automatically start the agent

        Returns:
            DeployedAgent instance
        """
        # Handle backward compatibility
        if agent_type is None and template is None:
            agent_type = AgentType.GENERAL

        config_dict = config or {}
        if agent_type:
            config_dict["agent_type"] = agent_type
        elif template:
            config_dict["template"] = template

        agent_config = AgentConfig(**config_dict)
        request = CreateAgentRequest(config=agent_config, auto_start=auto_start)

        response = self.client.post(
            f"{self.api_prefix}/agents",
            json=request.model_dump(),
        )
        response.raise_for_status()

        data = response.json()
        return DeployedAgent(
            client=self,
            agent_id=data["agent_id"],
            endpoint=data["endpoint"],
            status=data["status"],
        )

    def get_agent(self, agent_id: str) -> AgentInfo:
        """
        Get information about an agent

        Args:
            agent_id: Agent identifier

        Returns:
            AgentInfo object
        """
        response = self.client.get(f"{self.api_prefix}/agents/{agent_id}")
        response.raise_for_status()
        return AgentInfo(**response.json())

    def list_agents(self) -> Dict[str, AgentInfo]:
        """
        List all agents

        Returns:
            Dictionary of agent_id -> AgentInfo
        """
        response = self.client.get(f"{self.api_prefix}/agents")
        response.raise_for_status()
        data = response.json()
        return {agent_id: AgentInfo(**info) for agent_id, info in data.items()}

    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent

        Args:
            agent_id: Agent identifier

        Returns:
            True if deleted successfully
        """
        response = self.client.delete(f"{self.api_prefix}/agents/{agent_id}")
        response.raise_for_status()
        return True

    def send_message(
        self, agent_id: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Send a message to an agent

        Args:
            agent_id: Agent identifier
            message: Message to send
            context: Additional context

        Returns:
            AgentResponse object
        """
        response = self.client.post(
            f"{self.api_prefix}/agents/{agent_id}/messages",
            json={"message": message, "context": context or {}},
        )
        response.raise_for_status()
        return AgentResponse(**response.json())

    def start_agent(self, agent_id: str) -> bool:
        """Start an agent"""
        response = self.client.post(f"{self.api_prefix}/agents/{agent_id}/start")
        response.raise_for_status()
        return True

    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent"""
        response = self.client.post(f"{self.api_prefix}/agents/{agent_id}/stop")
        response.raise_for_status()
        return True

    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        response = self.client.get("/health")
        response.raise_for_status()
        return response.json()

    def list_agent_types(self) -> Dict[str, Any]:
        """
        List all available agent types and their configurations

        Returns:
            Dictionary of agent type information
        """
        response = self.client.get(f"{self.api_prefix}/agent-types")
        response.raise_for_status()
        return response.json()

    def quick_query(
        self, message: str, agent_type: AgentType = AgentType.GENERAL, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a quick query without managing agent lifecycle

        Args:
            message: Message to send
            agent_type: Type of agent to use for the query
            context: Additional context

        Returns:
            Agent response text
        """
        response = self.client.post(
            f"{self.api_prefix}/query",
            params={"agent_type": agent_type.value},
            json={"message": message, "context": context or {}},
        )
        response.raise_for_status()
        result = response.json()
        return result["response"]

    def close(self):
        """Close the client connection"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DeployedAgent:
    """Represents a deployed agent instance"""

    def __init__(self, client: AgentClient, agent_id: str, endpoint: str, status: str):
        self.client = client
        self.id = agent_id
        self.endpoint = endpoint
        self._status = status

    def send(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Send a message to the agent

        Args:
            message: Message to send
            context: Additional context

        Returns:
            Agent response text
        """
        response = self.client.send_message(self.id, message, context)
        return response.response

    def start(self) -> bool:
        """Start the agent"""
        return self.client.start_agent(self.id)

    def stop(self) -> bool:
        """Stop the agent"""
        return self.client.stop_agent(self.id)

    def delete(self) -> bool:
        """Delete the agent"""
        return self.client.delete_agent(self.id)

    def info(self) -> AgentInfo:
        """Get agent information"""
        return self.client.get_agent(self.id)

    @property
    def status(self) -> str:
        """Get current agent status"""
        info = self.info()
        return info.status

    def __repr__(self):
        return f"DeployedAgent(id={self.id}, status={self._status}, endpoint={self.endpoint})"
