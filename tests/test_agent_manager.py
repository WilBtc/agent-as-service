"""
Tests for Agent Manager
"""

import pytest
from aaas.agent_manager import AgentManager, ClaudeCodeAgent
from aaas.models import AgentConfig, AgentStatus


@pytest.fixture
def agent_manager():
    """Create an agent manager instance"""
    return AgentManager()


@pytest.fixture
def basic_config():
    """Create a basic agent configuration"""
    return AgentConfig(
        template="test-agent",
        language="en",
        personality="helpful"
    )


@pytest.mark.asyncio
async def test_create_agent(agent_manager, basic_config):
    """Test creating a new agent"""
    agent_id = await agent_manager.create_agent(basic_config, auto_start=False)

    assert agent_id is not None
    assert len(agent_id) > 0

    agent = await agent_manager.get_agent(agent_id)
    assert agent is not None
    assert agent.config.template == "test-agent"


@pytest.mark.asyncio
async def test_list_agents(agent_manager, basic_config):
    """Test listing agents"""
    # Create multiple agents
    agent_ids = []
    for i in range(3):
        config = AgentConfig(template=f"test-agent-{i}")
        agent_id = await agent_manager.create_agent(config, auto_start=False)
        agent_ids.append(agent_id)

    agents = await agent_manager.list_agents()
    assert len(agents) >= 3

    for agent_id in agent_ids:
        assert agent_id in agents


@pytest.mark.asyncio
async def test_delete_agent(agent_manager, basic_config):
    """Test deleting an agent"""
    agent_id = await agent_manager.create_agent(basic_config, auto_start=False)

    # Verify agent exists
    agent = await agent_manager.get_agent(agent_id)
    assert agent is not None

    # Delete agent
    success = await agent_manager.delete_agent(agent_id)
    assert success is True

    # Verify agent is gone
    agent = await agent_manager.get_agent(agent_id)
    assert agent is None


@pytest.mark.asyncio
async def test_max_agents_limit(agent_manager, basic_config):
    """Test maximum agents limit"""
    from aaas.config import settings
    original_max = settings.max_agents

    try:
        settings.max_agents = 2

        # Create max agents
        await agent_manager.create_agent(basic_config, auto_start=False)
        await agent_manager.create_agent(basic_config, auto_start=False)

        # Try to create one more
        with pytest.raises(ValueError, match="Maximum number of agents"):
            await agent_manager.create_agent(basic_config, auto_start=False)

    finally:
        settings.max_agents = original_max


@pytest.mark.asyncio
async def test_agent_info(agent_manager, basic_config):
    """Test getting agent information"""
    agent_id = await agent_manager.create_agent(basic_config, auto_start=False)
    agent = await agent_manager.get_agent(agent_id)

    info = agent.get_info()

    assert info.id == agent_id
    assert info.status == AgentStatus.STOPPED
    assert info.config.template == "test-agent"
    assert info.messages_count == 0
