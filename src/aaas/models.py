"""
Data models for AaaS
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    IDLE = "idle"
    RECOVERING = "recovering"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentType(str, Enum):
    """Agent type enumeration"""
    GENERAL = "general"
    RESEARCH = "research"
    CODE = "code"
    FINANCE = "finance"
    CUSTOMER_SUPPORT = "customer_support"
    PERSONAL_ASSISTANT = "personal_assistant"
    DATA_ANALYSIS = "data_analysis"
    CUSTOM = "custom"


class PermissionMode(str, Enum):
    """Permission mode for agent operations"""
    ASK = "ask"
    ACCEPT_EDITS = "acceptEdits"
    ACCEPT_ALL = "acceptAll"


class AgentConfig(BaseModel):
    """Configuration for an agent instance"""
    agent_type: AgentType = Field(default=AgentType.GENERAL, description="Type of agent to create")
    template: Optional[str] = Field(default=None, description="Agent template or type (deprecated, use agent_type)")
    language: Optional[str] = Field(default="en", description="Language for the agent")
    personality: Optional[str] = Field(default="professional", description="Agent personality")
    integration: Optional[str] = Field(default=None, description="External integration")
    max_tokens: Optional[int] = Field(default=4096, description="Maximum tokens per request")
    temperature: Optional[float] = Field(default=1.0, description="Temperature for responses")
    working_directory: Optional[str] = Field(default=None, description="Working directory for agent")
    environment: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")

    # Claude Agent SDK specific options
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt for the agent")
    allowed_tools: Optional[List[str]] = Field(default=None, description="List of allowed tool names")
    permission_mode: PermissionMode = Field(default=PermissionMode.ASK, description="Permission mode for agent operations")
    max_turns: Optional[int] = Field(default=None, description="Maximum number of conversation turns")
    model: Optional[str] = Field(default="claude-sonnet-4-5-20250929", description="Claude model to use")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "research",
                "language": "en",
                "personality": "professional",
                "max_tokens": 4096,
                "temperature": 1.0,
                "permission_mode": "acceptEdits",
                "model": "claude-sonnet-4-5-20250929"
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


# Agent type configurations
AGENT_TYPE_CONFIGS = {
    AgentType.GENERAL: {
        "description": "General-purpose agent for various tasks",
        "system_prompt": "You are a helpful AI assistant that can help with a wide variety of tasks.",
        "allowed_tools": ["Read", "Write", "Bash", "Glob", "Grep"],
        "permission_mode": PermissionMode.ASK,
    },
    AgentType.RESEARCH: {
        "description": "Deep research agent for comprehensive analysis",
        "system_prompt": """You are a research specialist agent. Your primary goal is to conduct comprehensive research across large document collections.

You excel at:
- Searching through file systems and documents
- Analyzing and synthesizing information from multiple sources
- Using both agentic search (grep, tail, etc.) for accurate context retrieval
- Providing well-structured, evidence-based research summaries

Always cite your sources and provide comprehensive analysis.""",
        "allowed_tools": ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Bash"],
        "permission_mode": PermissionMode.ACCEPT_EDITS,
    },
    AgentType.CODE: {
        "description": "Code development and review agent",
        "system_prompt": """You are a code specialist agent. Your primary goal is to help with software development tasks.

You excel at:
- Writing clean, maintainable code
- Reviewing code for bugs and best practices
- Refactoring and optimizing existing code
- Testing and debugging
- Following project conventions and style guidelines

Always prioritize code quality, security, and maintainability.""",
        "allowed_tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        "permission_mode": PermissionMode.ACCEPT_EDITS,
    },
    AgentType.FINANCE: {
        "description": "Finance analysis and portfolio management agent",
        "system_prompt": """You are a finance specialist agent. Your primary goal is to help with financial analysis and portfolio management.

You excel at:
- Analyzing portfolios and financial goals
- Evaluating investments and opportunities
- Accessing external financial APIs
- Running calculations and financial models
- Providing data-driven financial insights

Always provide well-reasoned financial analysis with supporting data.""",
        "allowed_tools": ["Read", "Write", "Bash", "WebSearch", "WebFetch"],
        "permission_mode": PermissionMode.ASK,
    },
    AgentType.CUSTOMER_SUPPORT: {
        "description": "Customer support and service agent",
        "system_prompt": """You are a customer support specialist agent. Your primary goal is to help with customer service tasks.

You excel at:
- Handling ambiguous customer requests
- Collecting and reviewing customer data
- Connecting to external APIs for customer information
- Providing helpful and empathetic responses
- Escalating to humans when necessary

Always be professional, empathetic, and solution-oriented.""",
        "allowed_tools": ["Read", "Write", "WebFetch"],
        "permission_mode": PermissionMode.ASK,
    },
    AgentType.PERSONAL_ASSISTANT: {
        "description": "Personal productivity and task management agent",
        "system_prompt": """You are a personal assistant agent. Your primary goal is to help with productivity and task management.

You excel at:
- Managing calendars and schedules
- Booking travel and appointments
- Organizing tasks and priorities
- Connecting to internal data sources
- Tracking context across multiple applications

Always be proactive, organized, and detail-oriented.""",
        "allowed_tools": ["Read", "Write", "WebSearch", "WebFetch"],
        "permission_mode": PermissionMode.ASK,
    },
    AgentType.DATA_ANALYSIS: {
        "description": "Data analysis and visualization agent",
        "system_prompt": """You are a data analysis specialist agent. Your primary goal is to help with data analysis and insights.

You excel at:
- Analyzing datasets and identifying patterns
- Running statistical calculations
- Creating data visualizations
- Providing data-driven insights and recommendations
- Working with various data formats and sources

Always provide clear, actionable insights backed by data.""",
        "allowed_tools": ["Read", "Write", "Bash", "Grep", "Glob"],
        "permission_mode": PermissionMode.ACCEPT_EDITS,
    },
    AgentType.CUSTOM: {
        "description": "Custom agent with user-defined configuration",
        "system_prompt": "You are a helpful AI assistant.",
        "allowed_tools": ["Read", "Write", "Bash", "Glob", "Grep"],
        "permission_mode": PermissionMode.ASK,
    },
}


def get_agent_config_for_type(agent_type: AgentType, custom_config: Optional[AgentConfig] = None) -> Dict[str, Any]:
    """Get the configuration for a specific agent type, optionally merging with custom config"""
    base_config = AGENT_TYPE_CONFIGS.get(agent_type, AGENT_TYPE_CONFIGS[AgentType.GENERAL]).copy()

    if custom_config:
        # Override with custom configuration if provided
        if custom_config.system_prompt:
            base_config["system_prompt"] = custom_config.system_prompt
        if custom_config.allowed_tools:
            base_config["allowed_tools"] = custom_config.allowed_tools
        if custom_config.permission_mode:
            base_config["permission_mode"] = custom_config.permission_mode

    return base_config
