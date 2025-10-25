"""
Agent as a Service (AaaS)
Enterprise AI Agent Platform - Powered by Claude Agent SDK

The Claude Agent SDK runs Claude Code as a subprocess, providing a robust
interface for managing multiple agent instances at scale.
"""

__version__ = "1.0.0"

from .client import AgentClient
from .models import AgentConfig, AgentStatus, AgentResponse, AgentType, PermissionMode

__all__ = [
    "AgentClient",
    "AgentConfig",
    "AgentStatus",
    "AgentResponse",
    "AgentType",
    "PermissionMode",
]
