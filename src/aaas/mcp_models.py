"""
MCP (Model Context Protocol) Server Models and Configuration

Defines MCP server types, configurations, and agent-to-MCP mappings
for adaptive provisioning.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MCPServerType(str, Enum):
    """Available MCP server types"""
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    POSTGRES = "postgres"
    SQLITE = "sqlite"
    WEB_SEARCH = "web_search"
    BROWSER = "browser"
    GIT = "git"
    GITHUB = "github"
    SLACK = "slack"
    GOOGLE_DRIVE = "google_drive"
    MEMORY = "memory"
    REDIS = "redis"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    SEQUENTIAL_THINKING = "sequential_thinking"
    PUPPETEER = "puppeteer"
    BRAVE_SEARCH = "brave_search"


class MCPServerStatus(str, Enum):
    """MCP server status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    server_type: MCPServerType = Field(description="Type of MCP server")
    command: str = Field(description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    shared: bool = Field(default=True, description="Can be shared across agents")
    max_connections: int = Field(default=10, description="Maximum concurrent connections")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    idle_timeout: int = Field(default=300, description="Idle timeout in seconds")
    required_env_vars: List[str] = Field(default_factory=list, description="Required environment variables")
    optional: bool = Field(default=False, description="Server is optional, don't fail if unavailable")


class MCPServerInfo(BaseModel):
    """Information about a running MCP server"""
    server_id: str = Field(description="Unique server identifier")
    server_type: MCPServerType = Field(description="Type of MCP server")
    status: MCPServerStatus = Field(description="Current server status")
    created_at: datetime = Field(description="Creation timestamp")
    last_health_check: Optional[datetime] = Field(default=None, description="Last health check time")
    connected_agents: List[str] = Field(default_factory=list, description="Connected agent IDs")
    connection_count: int = Field(default=0, description="Current number of connections")
    pid: Optional[int] = Field(default=None, description="Process ID")
    endpoint: Optional[str] = Field(default=None, description="Server endpoint/URL")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


# MCP Server Catalog - Available MCP servers and their configurations
MCP_SERVER_CATALOG: Dict[MCPServerType, MCPServerConfig] = {
    MCPServerType.FILESYSTEM: MCPServerConfig(
        server_type=MCPServerType.FILESYSTEM,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."],
        shared=True,
        max_connections=50,
        optional=False,
    ),
    MCPServerType.MEMORY: MCPServerConfig(
        server_type=MCPServerType.MEMORY,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        shared=True,
        max_connections=100,
        optional=False,
    ),
    MCPServerType.GIT: MCPServerConfig(
        server_type=MCPServerType.GIT,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-git"],
        shared=True,
        max_connections=20,
        optional=True,
    ),
    MCPServerType.GITHUB: MCPServerConfig(
        server_type=MCPServerType.GITHUB,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
        shared=True,
        max_connections=10,
        required_env_vars=["GITHUB_PERSONAL_ACCESS_TOKEN"],
        optional=True,
    ),
    MCPServerType.POSTGRES: MCPServerConfig(
        server_type=MCPServerType.POSTGRES,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres"],
        env={"POSTGRES_CONNECTION_STRING": ""},
        shared=True,
        max_connections=20,
        required_env_vars=["POSTGRES_CONNECTION_STRING"],
        optional=True,
    ),
    MCPServerType.SQLITE: MCPServerConfig(
        server_type=MCPServerType.SQLITE,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sqlite"],
        shared=True,
        max_connections=10,
        optional=True,
    ),
    MCPServerType.BRAVE_SEARCH: MCPServerConfig(
        server_type=MCPServerType.BRAVE_SEARCH,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": ""},
        shared=True,
        max_connections=50,
        required_env_vars=["BRAVE_API_KEY"],
        optional=True,
    ),
    MCPServerType.PUPPETEER: MCPServerConfig(
        server_type=MCPServerType.PUPPETEER,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
        shared=False,  # Each agent gets its own browser instance
        max_connections=1,
        optional=True,
    ),
    MCPServerType.SLACK: MCPServerConfig(
        server_type=MCPServerType.SLACK,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-slack"],
        env={"SLACK_BOT_TOKEN": "", "SLACK_TEAM_ID": ""},
        shared=True,
        max_connections=10,
        required_env_vars=["SLACK_BOT_TOKEN"],
        optional=True,
    ),
    MCPServerType.GOOGLE_DRIVE: MCPServerConfig(
        server_type=MCPServerType.GOOGLE_DRIVE,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-gdrive"],
        shared=True,
        max_connections=10,
        optional=True,
    ),
    MCPServerType.SEQUENTIAL_THINKING: MCPServerConfig(
        server_type=MCPServerType.SEQUENTIAL_THINKING,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
        shared=True,
        max_connections=50,
        optional=False,
    ),
}


# Agent Type to MCP Server Mappings
# Defines which MCP servers each agent type needs
AGENT_MCP_REQUIREMENTS: Dict[str, List[MCPServerType]] = {
    "general": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.SEQUENTIAL_THINKING,
    ],
    "research": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.BRAVE_SEARCH,
        MCPServerType.PUPPETEER,
        MCPServerType.SEQUENTIAL_THINKING,
        MCPServerType.GIT,
    ],
    "code": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.GIT,
        MCPServerType.GITHUB,
        MCPServerType.SEQUENTIAL_THINKING,
    ],
    "finance": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.BRAVE_SEARCH,
        MCPServerType.POSTGRES,
        MCPServerType.SEQUENTIAL_THINKING,
    ],
    "customer_support": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.SLACK,
        MCPServerType.SEQUENTIAL_THINKING,
    ],
    "personal_assistant": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.GOOGLE_DRIVE,
        MCPServerType.SEQUENTIAL_THINKING,
        MCPServerType.BRAVE_SEARCH,
    ],
    "data_analysis": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.POSTGRES,
        MCPServerType.SQLITE,
        MCPServerType.SEQUENTIAL_THINKING,
    ],
    "custom": [
        MCPServerType.FILESYSTEM,
        MCPServerType.MEMORY,
        MCPServerType.SEQUENTIAL_THINKING,
    ],
}


def get_mcp_servers_for_agent_type(agent_type: str) -> List[MCPServerType]:
    """
    Get the list of MCP servers required for a specific agent type.

    Args:
        agent_type: The agent type (e.g., 'research', 'code')

    Returns:
        List of MCPServerType enums
    """
    return AGENT_MCP_REQUIREMENTS.get(agent_type.lower(), [])


def get_mcp_server_config(server_type: MCPServerType) -> Optional[MCPServerConfig]:
    """
    Get the configuration for a specific MCP server type.

    Args:
        server_type: The MCP server type

    Returns:
        MCPServerConfig or None if not found
    """
    return MCP_SERVER_CATALOG.get(server_type)


def validate_mcp_server_env(server_type: MCPServerType, env: Dict[str, str]) -> bool:
    """
    Validate that required environment variables are present.

    Args:
        server_type: The MCP server type
        env: Environment variables dictionary

    Returns:
        True if all required env vars are present and non-empty
    """
    config = get_mcp_server_config(server_type)
    if not config:
        return False

    for var in config.required_env_vars:
        if var not in env or not env[var]:
            return False

    return True
