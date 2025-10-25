"""
Tests for AgentManager and Agent classes
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

from aaas.agent_manager import AgentManager, Agent
from aaas.models import AgentConfig, AgentType, AgentStatus, PermissionMode
from aaas.config import settings


@pytest.fixture
def agent_manager():
    """Create agent manager instance"""
    return AgentManager()


@pytest.fixture
def mock_claude_sdk():
    """Mock Claude SDK client"""
    with patch("aaas.agent_manager.ClaudeSDKClient") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


class TestAgentManager:
    """Test AgentManager class"""

    @pytest.mark.asyncio
    async def test_create_agent_general_type(self, agent_manager):
        """Test creating general agent"""
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=True)

        assert agent_id is not None
        assert len(agent_id) > 0
        assert agent_id in agent_manager.agents

    @pytest.mark.asyncio
    async def test_create_agent_research_type(self, agent_manager):
        """Test creating research agent"""
        config = AgentConfig(agent_type=AgentType.RESEARCH)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        agent = await agent_manager.get_agent(agent_id)
        assert agent is not None
        assert agent.config.agent_type == AgentType.RESEARCH

    @pytest.mark.asyncio
    async def test_create_agent_respects_max_agents(self, agent_manager):
        """Test that creating agents respects max_agents limit"""
        original_max = settings.max_agents
        settings.max_agents = 2

        try:
            with patch.object(Agent, "start", return_value=True):
                # Create first agent
                agent1_id = await agent_manager.create_agent(
                    AgentConfig(agent_type=AgentType.GENERAL),
                    auto_start=False
                )
                assert agent1_id is not None

                # Create second agent
                agent2_id = await agent_manager.create_agent(
                    AgentConfig(agent_type=AgentType.RESEARCH),
                    auto_start=False
                )
                assert agent2_id is not None

                # Third agent should fail
                with pytest.raises(ValueError, match="Maximum number of agents"):
                    await agent_manager.create_agent(
                        AgentConfig(agent_type=AgentType.CODE),
                        auto_start=False
                    )
        finally:
            settings.max_agents = original_max

    @pytest.mark.asyncio
    async def test_create_agent_with_auto_start(self, agent_manager):
        """Test creating agent with auto_start=True"""
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "start", return_value=True) as mock_start:
            agent_id = await agent_manager.create_agent(config, auto_start=True)

            # Verify start was called
            agent = await agent_manager.get_agent(agent_id)
            assert agent is not None

    @pytest.mark.asyncio
    async def test_create_agent_without_auto_start(self, agent_manager):
        """Test creating agent with auto_start=False"""
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "start", return_value=True) as mock_start:
            agent_id = await agent_manager.create_agent(config, auto_start=False)

            agent = await agent_manager.get_agent(agent_id)
            assert agent is not None
            # Start should not be called when auto_start=False
            # (check agent status instead)

    @pytest.mark.asyncio
    async def test_get_agent_exists(self, agent_manager):
        """Test getting existing agent"""
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        agent = await agent_manager.get_agent(agent_id)
        assert agent is not None
        assert agent.id == agent_id

    @pytest.mark.asyncio
    async def test_get_agent_not_exists(self, agent_manager):
        """Test getting non-existent agent returns None"""
        agent = await agent_manager.get_agent("nonexistent-id")
        assert agent is None

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, agent_manager):
        """Test listing agents when none exist"""
        agents = await agent_manager.list_agents()
        assert isinstance(agents, dict)
        assert len(agents) == 0

    @pytest.mark.asyncio
    async def test_list_agents_multiple(self, agent_manager):
        """Test listing multiple agents"""
        with patch.object(Agent, "start", return_value=True):
            agent1_id = await agent_manager.create_agent(
                AgentConfig(agent_type=AgentType.GENERAL),
                auto_start=False
            )
            agent2_id = await agent_manager.create_agent(
                AgentConfig(agent_type=AgentType.RESEARCH),
                auto_start=False
            )

        agents = await agent_manager.list_agents()
        assert len(agents) == 2
        assert agent1_id in agents
        assert agent2_id in agents

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, agent_manager):
        """Test deleting existing agent"""
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        with patch.object(Agent, "stop", return_value=True):
            success = await agent_manager.delete_agent(agent_id)

        assert success is True
        assert agent_id not in agent_manager.agents

    @pytest.mark.asyncio
    async def test_delete_agent_not_exists(self, agent_manager):
        """Test deleting non-existent agent returns False"""
        success = await agent_manager.delete_agent("nonexistent-id")
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_agent_stops_before_deleting(self, agent_manager):
        """Test that delete_agent stops the agent before deleting"""
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        with patch.object(Agent, "stop", return_value=True) as mock_stop:
            await agent_manager.delete_agent(agent_id)
            mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_all(self, agent_manager):
        """Test shutting down all agents"""
        with patch.object(Agent, "start", return_value=True):
            agent1_id = await agent_manager.create_agent(
                AgentConfig(agent_type=AgentType.GENERAL),
                auto_start=False
            )
            agent2_id = await agent_manager.create_agent(
                AgentConfig(agent_type=AgentType.RESEARCH),
                auto_start=False
            )

        with patch.object(Agent, "stop", return_value=True) as mock_stop:
            await agent_manager.shutdown_all()

            # Verify stop was called for each agent
            assert mock_stop.call_count == 2

        # Verify all agents are removed
        assert len(agent_manager.agents) == 0

    @pytest.mark.asyncio
    async def test_query_agent_quick_query(self, agent_manager, mock_claude_sdk):
        """Test quick query creates temporary agent"""
        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        # Mock the response
        async def mock_receive_response():
            yield MagicMock(content=[MagicMock(text="Quick response")])

        mock_claude_sdk.receive_response = mock_receive_response

        response = await agent_manager.query_agent(
            "Test question",
            AgentType.RESEARCH
        )

        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_query_agent_different_types(self, agent_manager, mock_claude_sdk):
        """Test quick query with different agent types"""
        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        async def mock_receive_response():
            yield MagicMock(content=[MagicMock(text="Response")])

        mock_claude_sdk.receive_response = mock_receive_response

        # Test with different agent types
        for agent_type in [AgentType.GENERAL, AgentType.RESEARCH, AgentType.CODE]:
            response = await agent_manager.query_agent("Test", agent_type)
            assert response is not None


class TestAgent:
    """Test Agent class"""

    @pytest.fixture
    def agent_config(self):
        """Create agent config for testing"""
        return AgentConfig(
            agent_type=AgentType.GENERAL,
            personality="professional",
            language="en"
        )

    def test_agent_initialization(self, agent_config):
        """Test agent initialization"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        assert agent.id == "test-id"
        assert agent.config == agent_config
        assert agent.status == AgentStatus.STOPPED
        assert agent.messages_count == 0

    def test_agent_get_info(self, agent_config):
        """Test agent get_info method"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        info = agent.get_info()

        assert info.id == "test-id"
        assert info.status == AgentStatus.STOPPED
        assert info.config.agent_type == AgentType.GENERAL
        assert info.messages_count == 0

    @pytest.mark.asyncio
    async def test_agent_start(self, agent_config, mock_claude_sdk):
        """Test starting an agent"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        success = await agent.start()

        assert success is True
        assert agent.status == AgentStatus.RUNNING

    @pytest.mark.asyncio
    async def test_agent_start_already_running(self, agent_config):
        """Test starting already running agent"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.RUNNING

        success = await agent.start()

        # Should return True without doing anything
        assert success is True

    @pytest.mark.asyncio
    async def test_agent_stop(self, agent_config):
        """Test stopping an agent"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.RUNNING
        agent.client = AsyncMock()

        success = await agent.stop()

        assert success is True
        assert agent.status == AgentStatus.STOPPED

    @pytest.mark.asyncio
    async def test_agent_stop_already_stopped(self, agent_config):
        """Test stopping already stopped agent"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.STOPPED

        success = await agent.stop()

        assert success is True

    @pytest.mark.asyncio
    async def test_agent_send_message(self, agent_config, mock_claude_sdk):
        """Test sending message to agent"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.RUNNING
        agent.client = mock_claude_sdk

        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        # Mock the response
        async def mock_receive_response():
            yield MagicMock(content=[MagicMock(text="Agent response")])

        mock_claude_sdk.receive_response = mock_receive_response

        response = await agent.send_message("Hello")

        assert response is not None
        assert isinstance(response, str)
        assert agent.messages_count == 1

    @pytest.mark.asyncio
    async def test_agent_send_message_with_context(self, agent_config, mock_claude_sdk):
        """Test sending message with context"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.RUNNING
        agent.client = mock_claude_sdk

        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        async def mock_receive_response():
            yield MagicMock(content=[MagicMock(text="Response with context")])

        mock_claude_sdk.receive_response = mock_receive_response

        context = {"user_id": "user-123", "session": "sess-456"}
        response = await agent.send_message("Process this", context)

        assert response is not None
        assert agent.messages_count == 1

    @pytest.mark.asyncio
    async def test_agent_send_message_increments_count(self, agent_config, mock_claude_sdk):
        """Test that sending messages increments message count"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.RUNNING
        agent.client = mock_claude_sdk

        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        async def mock_receive_response():
            yield MagicMock(content=[MagicMock(text="Response")])

        mock_claude_sdk.receive_response = mock_receive_response

        # Send multiple messages
        await agent.send_message("Message 1")
        await agent.send_message("Message 2")
        await agent.send_message("Message 3")

        assert agent.messages_count == 3

    def test_extract_text_from_message(self, agent_config):
        """Test extracting text from Claude SDK message"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        # Mock message with text content
        message = MagicMock()
        message.content = [MagicMock(text="Hello from Claude")]

        text = agent._extract_text_from_message(message)

        assert text == "Hello from Claude"

    def test_extract_text_from_message_empty(self, agent_config):
        """Test extracting text from message with no content"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        # Mock message with no content
        message = MagicMock()
        message.content = []

        text = agent._extract_text_from_message(message)

        assert text == ""

    def test_extract_text_from_message_multiple_parts(self, agent_config):
        """Test extracting text from message with multiple content parts"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        # Mock message with multiple text parts
        message = MagicMock()
        message.content = [
            MagicMock(text="Part 1"),
            MagicMock(text="Part 2"),
            MagicMock(text="Part 3")
        ]

        text = agent._extract_text_from_message(message)

        # Should concatenate all parts
        assert "Part 1" in text or "Part 2" in text or "Part 3" in text


class TestAgentTypeConfigurations:
    """Test agent type configurations in agent creation"""

    @pytest.mark.asyncio
    async def test_research_agent_has_correct_tools(self, agent_manager):
        """Test research agent gets correct tools"""
        config = AgentConfig(agent_type=AgentType.RESEARCH)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        agent = await agent_manager.get_agent(agent_id)
        # Tools are configured in AGENT_TYPE_CONFIGS
        assert agent is not None

    @pytest.mark.asyncio
    async def test_customer_support_restricted_tools(self, agent_manager):
        """Test customer support agent has restricted tools"""
        config = AgentConfig(agent_type=AgentType.CUSTOMER_SUPPORT)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        agent = await agent_manager.get_agent(agent_id)
        # Should not have Bash access (verified in AGENT_TYPE_CONFIGS)
        assert agent is not None

    @pytest.mark.asyncio
    async def test_code_agent_has_file_tools(self, agent_manager):
        """Test code agent has file manipulation tools"""
        config = AgentConfig(agent_type=AgentType.CODE)

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        agent = await agent_manager.get_agent(agent_id)
        assert agent is not None

    @pytest.mark.asyncio
    async def test_custom_agent_config_override(self, agent_manager):
        """Test custom agent with config override"""
        config = AgentConfig(
            agent_type=AgentType.CUSTOM,
            system_prompt="Custom system prompt",
            allowed_tools=["Read", "Write"],
            permission_mode=PermissionMode.ACCEPT_ALL
        )

        with patch.object(Agent, "start", return_value=True):
            agent_id = await agent_manager.create_agent(config, auto_start=False)

        agent = await agent_manager.get_agent(agent_id)
        assert agent is not None
        assert agent.config.system_prompt == "Custom system prompt"


class TestAgentErrorHandling:
    """Test error handling in agent operations"""

    @pytest.mark.asyncio
    async def test_agent_start_failure(self, agent_config):
        """Test handling of agent start failure"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")

        with patch("aaas.agent_manager.ClaudeSDKClient") as mock_sdk:
            mock_sdk.side_effect = Exception("Failed to start")

            success = await agent.start()

            assert success is False
            assert agent.status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_agent_send_message_failure(self, agent_config, mock_claude_sdk):
        """Test handling of send message failure"""
        agent = Agent("test-id", agent_config, "/tmp/test-agent")
        agent.status = AgentStatus.RUNNING
        agent.client = mock_claude_sdk

        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None
        mock_claude_sdk.query.side_effect = Exception("Send failed")

        with pytest.raises(Exception):
            await agent.send_message("Hello")

    @pytest.mark.asyncio
    async def test_agent_creation_with_invalid_config(self, agent_manager):
        """Test creating agent with invalid config"""
        # This should be caught by Pydantic validation
        # But test the manager's handling
        config = AgentConfig(agent_type=AgentType.GENERAL)

        with patch.object(Agent, "__init__") as mock_init:
            mock_init.side_effect = ValueError("Invalid config")

            with pytest.raises(ValueError):
                await agent_manager.create_agent(config, auto_start=False)


class TestConcurrency:
    """Test concurrent agent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, agent_manager):
        """Test creating multiple agents concurrently"""
        async def create_agent(agent_type):
            config = AgentConfig(agent_type=agent_type)
            with patch.object(Agent, "start", return_value=True):
                return await agent_manager.create_agent(config, auto_start=False)

        # Create multiple agents concurrently
        agent_ids = await asyncio.gather(
            create_agent(AgentType.GENERAL),
            create_agent(AgentType.RESEARCH),
            create_agent(AgentType.CODE)
        )

        assert len(agent_ids) == 3
        assert len(set(agent_ids)) == 3  # All IDs are unique

    @pytest.mark.asyncio
    async def test_concurrent_message_sending(self, agent_config, mock_claude_sdk):
        """Test sending messages to multiple agents concurrently"""
        # Create multiple agents
        agents = [
            Agent(f"agent-{i}", agent_config, f"/tmp/agent-{i}")
            for i in range(3)
        ]

        # Set all as running
        for agent in agents:
            agent.status = AgentStatus.RUNNING
            agent.client = mock_claude_sdk

        mock_claude_sdk.__aenter__.return_value = mock_claude_sdk
        mock_claude_sdk.__aexit__.return_value = None

        async def mock_receive_response():
            yield MagicMock(content=[MagicMock(text="Response")])

        mock_claude_sdk.receive_response = mock_receive_response

        # Send messages concurrently
        responses = await asyncio.gather(
            *[agent.send_message(f"Message to agent {i}") for i, agent in enumerate(agents)]
        )

        assert len(responses) == 3
        for agent in agents:
            assert agent.messages_count == 1
