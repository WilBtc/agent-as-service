"""
Configuration management for AaaS
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    api_prefix: str = "/api/v1"

    # Claude Code Configuration
    claude_code_path: str = "claude"  # Assumes claude is in PATH
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5-20250929"

    # Agent Configuration
    max_agents: int = 100
    min_agents: int = 1
    agent_timeout: int = 3600  # 1 hour
    agent_idle_timeout: int = 300  # 5 minutes
    agent_start_timeout: int = 60  # 60 seconds for agent startup
    max_turns: int = 25
    default_working_dir: str = "/tmp/aaas-agents"

    # Storage
    data_dir: Path = Path("./data")
    logs_dir: Path = Path("./logs")

    # Security
    api_key_header: str = "X-API-Key"
    api_key: Optional[str] = None  # API key for authentication (set via AAAS_API_KEY env var)
    require_api_key: bool = False  # Set to True to enable API key authentication
    allowed_origins: list = ["*"]

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60  # Max requests per minute per IP
    rate_limit_agent_creation: int = 10  # Max agent creations per minute

    # Auto-scaling
    enable_autoscaling: bool = True
    scale_up_threshold: float = 0.8  # Scale at 80% capacity
    scale_down_threshold: float = 0.3  # Scale down at 30% capacity

    # Health Monitoring
    enable_health_monitoring: bool = True
    health_check_interval: int = 30  # seconds
    enable_auto_recovery: bool = True
    max_recovery_attempts: int = 3
    recovery_backoff_seconds: int = 5

    # MCP Server Configuration
    # Disabled by default until subprocess management is fully implemented
    # Set AAAS_ENABLE_MCP_SERVERS=true to enable
    enable_mcp_servers: bool = False  # Enable adaptive MCP server provisioning
    mcp_server_idle_timeout: int = 300  # Idle timeout for MCP servers (5 minutes)
    mcp_server_health_check_interval: int = 60  # Health check interval for MCP servers

    # Idle Management
    enable_idle_shutdown: bool = True

    # Monitoring & Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090
    enable_structured_logging: bool = True

    # Environment
    environment: str = "production"  # dev, staging, production

    # Resource Limits
    max_memory_per_agent_mb: int = 512
    max_cpu_per_agent_percent: float = 25.0

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def init_directories():
    """Initialize required directories"""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.default_working_dir).mkdir(parents=True, exist_ok=True)
