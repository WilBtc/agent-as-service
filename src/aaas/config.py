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
    agent_timeout: int = 3600  # 1 hour
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
