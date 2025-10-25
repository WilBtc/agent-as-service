"""
Shared pytest fixtures and configuration for all tests
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from typing import AsyncGenerator, Generator

from aaas.models import AgentConfig, AgentType, PermissionMode
from aaas.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings to defaults before each test"""
    original_values = {}

    # Save original values
    for attr in dir(settings):
        if not attr.startswith("_"):
            try:
                original_values[attr] = getattr(settings, attr)
            except:
                pass

    yield

    # Restore original values
    for attr, value in original_values.items():
        try:
            setattr(settings, attr, value)
        except:
            pass


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    def set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, str(value))

    return set_env


@pytest.fixture
def disable_auth():
    """Disable authentication for testing"""
    original = settings.require_api_key
    settings.require_api_key = False
    yield
    settings.require_api_key = original


@pytest.fixture
def enable_auth():
    """Enable authentication for testing"""
    original_require = settings.require_api_key
    original_key = settings.api_key

    settings.require_api_key = True
    settings.api_key = "test-api-key-12345"

    yield "test-api-key-12345"

    settings.require_api_key = original_require
    settings.api_key = original_key


@pytest.fixture
def disable_rate_limiting():
    """Disable rate limiting for testing"""
    original = settings.rate_limit_enabled
    settings.rate_limit_enabled = False
    yield
    settings.rate_limit_enabled = original


@pytest.fixture
def enable_rate_limiting():
    """Enable rate limiting for testing"""
    original = settings.rate_limit_enabled
    settings.rate_limit_enabled = True
    yield
    settings.rate_limit_enabled = original


@pytest.fixture
def sample_agent_config():
    """Create a sample agent configuration"""
    return AgentConfig(
        agent_type=AgentType.GENERAL,
        personality="professional",
        language="en",
        max_tokens=4096,
        temperature=1.0
    )


@pytest.fixture
def sample_research_config():
    """Create a sample research agent configuration"""
    return AgentConfig(
        agent_type=AgentType.RESEARCH,
        personality="analytical",
        language="en",
        max_tokens=8192,
        temperature=0.7
    )


@pytest.fixture
def sample_code_config():
    """Create a sample code agent configuration"""
    return AgentConfig(
        agent_type=AgentType.CODE,
        personality="precise",
        language="en",
        permission_mode=PermissionMode.ACCEPT_EDITS
    )


@pytest.fixture
def sample_custom_config():
    """Create a sample custom agent configuration"""
    return AgentConfig(
        agent_type=AgentType.CUSTOM,
        system_prompt="You are a custom agent for testing",
        allowed_tools=["Read", "Write"],
        permission_mode=PermissionMode.ASK
    )


@pytest.fixture
def mock_claude_client():
    """Mock Claude SDK client"""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    # Mock receive_response as async generator
    async def mock_receive():
        yield MagicMock(content=[MagicMock(text="Mocked response")])

    client.receive_response = mock_receive
    client.query = AsyncMock()

    return client


@pytest.fixture
def mock_agent():
    """Create a mock agent"""
    agent = AsyncMock()
    agent.id = "test-agent-123"
    agent.status = "running"
    agent.messages_count = 0
    agent.config = AgentConfig(agent_type=AgentType.GENERAL)
    agent.get_info = MagicMock(return_value={
        "id": "test-agent-123",
        "status": "running",
        "messages_count": 0,
        "config": {"agent_type": "general"}
    })
    agent.start = AsyncMock(return_value=True)
    agent.stop = AsyncMock(return_value=True)
    agent.send_message = AsyncMock(return_value="Mocked response")

    return agent


@pytest.fixture
async def cleanup_agents():
    """Cleanup function to remove test agents after tests"""
    agent_ids = []

    def register_agent(agent_id: str):
        agent_ids.append(agent_id)

    yield register_agent

    # Cleanup after test
    from aaas.agent_manager import get_agent_manager
    manager = get_agent_manager()
    for agent_id in agent_ids:
        try:
            await manager.delete_agent(agent_id)
        except:
            pass


@pytest.fixture
def api_headers():
    """Default API headers for requests"""
    return {
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key-12345"
    }


@pytest.fixture
def sample_message_request():
    """Sample message request payload"""
    return {
        "message": "Test message",
        "context": {"user_id": "test-user"}
    }


@pytest.fixture
def sample_create_agent_request():
    """Sample create agent request payload"""
    return {
        "config": {
            "agent_type": "general",
            "personality": "professional",
            "language": "en"
        },
        "auto_start": True
    }


# Pytest configuration hooks

def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Register custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for multiple components"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication tests"
    )
    config.addinivalue_line(
        "markers", "rate_limit: Rate limiting tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add markers based on test location
        if "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)

        if "test_auth" in item.nodeid or "authentication" in item.name.lower():
            item.add_marker(pytest.mark.auth)

        if "rate_limit" in item.name.lower():
            item.add_marker(pytest.mark.rate_limit)

        # Mark asyncio tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
