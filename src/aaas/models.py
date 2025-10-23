"""
Data models for AaaS
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentConfig(BaseModel):
    """Configuration for an agent instance"""
    template: str = Field(description="Agent template or type")
    language: Optional[str] = Field(default="en", description="Language for the agent")
    personality: Optional[str] = Field(default="professional", description="Agent personality")
    integration: Optional[str] = Field(default=None, description="External integration")
    max_tokens: Optional[int] = Field(default=4096, description="Maximum tokens per request")
    temperature: Optional[float] = Field(default=1.0, description="Temperature for responses")
    working_directory: Optional[str] = Field(default=None, description="Working directory for agent")
    environment: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")

    class Config:
        json_schema_extra = {
            "example": {
                "template": "customer-service-pro",
                "language": "en",
                "personality": "professional",
                "integration": "zendesk",
                "max_tokens": 4096,
                "temperature": 1.0
            }
        }


class AgentInfo(BaseModel):
    """Information about a running agent"""
    id: str = Field(description="Unique agent identifier")
    status: AgentStatus = Field(description="Current agent status")
    config: AgentConfig = Field(description="Agent configuration")
    created_at: datetime = Field(description="Creation timestamp")
    endpoint: str = Field(description="Agent endpoint URL")
    pid: Optional[int] = Field(default=None, description="Process ID")
    messages_count: int = Field(default=0, description="Number of messages processed")


class AgentResponse(BaseModel):
    """Response from an agent"""
    agent_id: str = Field(description="Agent identifier")
    response: str = Field(description="Agent response text")
    timestamp: datetime = Field(description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MessageRequest(BaseModel):
    """Request to send a message to an agent"""
    message: str = Field(description="Message to send to the agent")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class CreateAgentRequest(BaseModel):
    """Request to create a new agent"""
    config: AgentConfig = Field(description="Agent configuration")
    auto_start: bool = Field(default=True, description="Automatically start the agent")


class CreateAgentResponse(BaseModel):
    """Response when creating an agent"""
    agent_id: str = Field(description="Created agent identifier")
    status: AgentStatus = Field(description="Agent status")
    endpoint: str = Field(description="Agent endpoint URL")
    message: str = Field(description="Status message")
