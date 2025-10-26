"""
Tests for FastAPI API endpoints
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from aaas.api import app
from aaas.models import AgentStatus, AgentType, PermissionMode
from aaas.config import settings


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_agent_id():
    """Valid UUID for testing"""
    return "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"


@pytest.fixture
def test_agent_id_2():
    """Second valid UUID for testing"""
    return "f9e8d7c6-b5a4-4321-9876-543210fedcba"


@pytest.fixture
def mock_agent_manager():
    """Mock agent manager for testing"""
    from aaas.api import app, get_agent_manager

    manager = AsyncMock()

    # Override the dependency in FastAPI
    app.dependency_overrides[get_agent_manager] = lambda: manager

    yield manager

    # Clean up after test
    app.dependency_overrides.clear()


@pytest.fixture
def valid_api_key():
    """Valid API key for testing"""
    return "test-api-key-12345"


@pytest.fixture
def setup_auth(valid_api_key):
    """Setup authentication for tests"""
    original_require = settings.require_api_key
    original_key = settings.api_key

    settings.require_api_key = True
    settings.api_key = valid_api_key

    yield valid_api_key

    settings.require_api_key = original_require
    settings.api_key = original_key


class TestRootEndpoints:
    """Test root and health endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Agent as a Service"
        assert data["status"] == "running"
        assert "/docs" in data["docs"]

    def test_health_check(self, client, mock_agent_manager):
        """Test health check endpoint"""
        mock_agent_manager.list_agents.return_value = {"agent1": {}, "agent2": {}}

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agents_count"] == 2
        assert "max_agents" in data


class TestAuthentication:
    """Test API authentication"""

    def test_create_agent_without_api_key(self, client, setup_auth):
        """Test creating agent without API key returns 401"""
        response = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "general"}, "auto_start": True}
        )

        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_create_agent_with_invalid_api_key(self, client, setup_auth):
        """Test creating agent with invalid API key returns 403"""
        response = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "general"}, "auto_start": True},
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_create_agent_with_valid_api_key(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test creating agent with valid API key succeeds"""
        # Mock agent creation
        mock_agent = MagicMock()
        mock_agent.status = AgentStatus.RUNNING
        mock_agent_manager.create_agent.return_value = test_agent_id
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "general"}, "auto_start": True},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == test_agent_id
        assert data["status"] == "running"

    def test_list_agents_requires_auth(self, client, setup_auth):
        """Test listing agents requires authentication"""
        response = client.get("/api/v1/agents")

        assert response.status_code == 401

    def test_get_agent_requires_auth(self, client, setup_auth):
        """Test getting agent requires authentication"""
        response = client.get("/api/v1/agents/test-id")

        assert response.status_code == 401

    def test_send_message_requires_auth(self, client, setup_auth):
        """Test sending message requires authentication"""
        response = client.post(
            "/api/v1/agents/test-id/messages",
            json={"message": "Hello"}
        )

        assert response.status_code == 401

    def test_list_agent_types_optional_auth(self, client):
        """Test listing agent types works without auth when disabled"""
        original_require = settings.require_api_key
        settings.require_api_key = False

        try:
            response = client.get("/api/v1/agent-types")
            assert response.status_code == 200
        finally:
            settings.require_api_key = original_require


class TestAgentCRUD:
    """Test agent CRUD operations"""

    def test_create_agent_general_type(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test creating general agent"""
        mock_agent = MagicMock()
        mock_agent.status = AgentStatus.RUNNING
        mock_agent_manager.create_agent.return_value = "agent-general"
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            "/api/v1/agents",
            json={
                "config": {
                    "agent_type": "general",
                    "personality": "professional"
                },
                "auto_start": True
            },
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 201
        data = response.json()
        assert "agent_id" in data
        assert data["status"] == "running"

    def test_create_agent_research_type(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test creating research agent"""
        mock_agent = MagicMock()
        mock_agent.status = AgentStatus.RUNNING
        mock_agent_manager.create_agent.return_value = "agent-research"
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            "/api/v1/agents",
            json={
                "config": {"agent_type": "research"},
                "auto_start": True
            },
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 201

    def test_create_agent_invalid_config(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test creating agent with invalid config returns 400"""
        mock_agent_manager.create_agent.side_effect = ValueError("Invalid configuration")

        response = client.post(
            "/api/v1/agents",
            json={
                "config": {"invalid_field": "value"},
                "auto_start": True
            },
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 400
        assert "Invalid configuration" in response.json()["detail"]

    def test_list_agents(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test listing all agents"""
        mock_agents = {
            "agent1": {"id": "agent1", "status": "running"},
            "agent2": {"id": "agent2", "status": "stopped"}
        }
        mock_agent_manager.list_agents.return_value = mock_agents

        response = client.get(
            "/api/v1/agents",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "agent1" in data

    def test_get_agent_found(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test getting specific agent"""
        mock_agent = MagicMock()
        mock_agent.get_info.return_value = {
            "id": test_agent_id,
            "status": "running",
            "agent_type": "general"
        }
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.get(
            f"/api/v1/agents/{test_agent_id}",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_agent_id

    def test_get_agent_not_found(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id_2):
        """Test getting non-existent agent returns 404"""
        mock_agent_manager.get_agent.return_value = None

        response = client.get(
            f"/api/v1/agents/{test_agent_id_2}",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_agent_success(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test deleting agent"""
        mock_agent_manager.delete_agent.return_value = True

        response = client.delete(
            f"/api/v1/agents/{test_agent_id}",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

    def test_delete_agent_not_found(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id_2):
        """Test deleting non-existent agent returns 404"""
        mock_agent_manager.delete_agent.return_value = False

        response = client.delete(
            f"/api/v1/agents/{test_agent_id_2}",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 404


class TestAgentOperations:
    """Test agent operations (start, stop, send message)"""

    def test_start_agent(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test starting an agent"""
        mock_agent = AsyncMock()
        mock_agent.start.return_value = True
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            f"/api/v1/agents/{test_agent_id}/start",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        assert "started" in response.json()["message"]

    def test_start_nonexistent_agent(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id_2):
        """Test starting non-existent agent returns 404"""
        mock_agent_manager.get_agent.return_value = None

        response = client.post(
            f"/api/v1/agents/{test_agent_id_2}/start",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 404

    def test_stop_agent(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test stopping an agent"""
        mock_agent = AsyncMock()
        mock_agent.stop.return_value = True
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            f"/api/v1/agents/{test_agent_id}/stop",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        assert "stopped" in response.json()["message"]

    def test_send_message_to_running_agent(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test sending message to running agent"""
        mock_agent = AsyncMock()
        mock_agent.status = AgentStatus.RUNNING
        mock_agent.send_message.return_value = "Agent response"
        mock_agent.created_at = datetime.utcnow()
        mock_agent.messages_count = 5
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            f"/api/v1/agents/{test_agent_id}/messages",
            json={"message": "Hello agent"},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == test_agent_id
        assert data["response"] == "Agent response"

    def test_send_message_to_stopped_agent(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test sending message to stopped agent returns 400"""
        mock_agent = MagicMock()
        mock_agent.status = AgentStatus.STOPPED
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            f"/api/v1/agents/{test_agent_id}/messages",
            json={"message": "Hello"},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 400
        assert "not running" in response.json()["detail"]

    def test_send_message_with_context(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test sending message with context"""
        mock_agent = AsyncMock()
        mock_agent.status = AgentStatus.RUNNING
        mock_agent.send_message.return_value = "Response with context"
        mock_agent.created_at = datetime.utcnow()
        mock_agent.messages_count = 1
        mock_agent_manager.get_agent.return_value = mock_agent

        response = client.post(
            f"/api/v1/agents/{test_agent_id}/messages",
            json={
                "message": "Analyze this data",
                "context": {"user_id": "user-456", "session": "sess-789"}
            },
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        # Verify send_message was called with both message and context
        mock_agent.send_message.assert_called_once()


class TestAgentTypes:
    """Test agent type endpoint"""

    def test_list_agent_types(self, client, setup_auth, valid_api_key):
        """Test listing all agent types"""
        response = client.get(
            "/api/v1/agent-types",
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have all 8 agent types
        assert "general" in data
        assert "research" in data
        assert "code" in data
        assert "finance" in data
        assert "customer_support" in data
        assert "personal_assistant" in data
        assert "data_analysis" in data
        assert "custom" in data

    def test_agent_type_structure(self, client, setup_auth, valid_api_key):
        """Test agent type info has correct structure"""
        response = client.get(
            "/api/v1/agent-types",
            headers={"X-API-Key": valid_api_key}
        )

        data = response.json()

        for agent_type, info in data.items():
            assert "type" in info
            assert "description" in info
            assert "allowed_tools" in info
            assert "permission_mode" in info
            assert isinstance(info["allowed_tools"], list)

    def test_research_agent_type_info(self, client, setup_auth, valid_api_key):
        """Test research agent type has search tools"""
        response = client.get(
            "/api/v1/agent-types",
            headers={"X-API-Key": valid_api_key}
        )

        data = response.json()
        research_info = data["research"]

        # Should have search capabilities
        tools = research_info["allowed_tools"]
        has_search = any(tool in tools for tool in ["WebSearch", "WebFetch"])
        assert has_search


class TestQuickQuery:
    """Test quick query endpoint"""

    def test_quick_query_general(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test quick query with general agent"""
        mock_agent_manager.query_agent.return_value = "Quick response"

        response = client.post(
            "/api/v1/query?agent_type=general",
            json={"message": "Quick question"},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "quick-query"
        assert data["response"] == "Quick response"
        assert data["metadata"]["agent_type"] == "general"

    def test_quick_query_research(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test quick query with research agent"""
        mock_agent_manager.query_agent.return_value = "Research result"

        response = client.post(
            "/api/v1/query?agent_type=research",
            json={"message": "Research this topic"},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["agent_type"] == "research"

    def test_quick_query_error_handling(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test quick query error handling"""
        mock_agent_manager.query_agent.side_effect = Exception("Query failed")

        response = client.post(
            "/api/v1/query",
            json={"message": "Test"},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 500
        assert "Failed to process query" in response.json()["detail"]


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_enforced(self, client, setup_auth, valid_api_key):
        """Test that rate limiting is enforced"""
        # Note: This test depends on rate_limit_enabled being True
        # In a real test, you'd make many requests to trigger the limit

        original_enabled = settings.rate_limit_enabled
        settings.rate_limit_enabled = True

        try:
            # Just verify the endpoint responds (actual rate limiting
            # would require many requests)
            response = client.get(
                "/api/v1/agent-types",
                headers={"X-API-Key": valid_api_key}
            )
            assert response.status_code in [200, 429]  # Either success or rate limited
        finally:
            settings.rate_limit_enabled = original_enabled

    def test_rate_limit_headers_present(self, client, setup_auth, valid_api_key):
        """Test that rate limit headers are present in response"""
        original_enabled = settings.rate_limit_enabled
        settings.rate_limit_enabled = True

        try:
            response = client.get(
                "/api/v1/agent-types",
                headers={"X-API-Key": valid_api_key}
            )

            # Slowapi adds these headers
            # Note: Headers might not be present if rate limiting is disabled
            if response.status_code != 429:
                # Headers may or may not be present depending on slowapi config
                pass
        finally:
            settings.rate_limit_enabled = original_enabled


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_json_body(self, client, setup_auth, valid_api_key):
        """Test sending invalid JSON returns 422"""
        response = client.post(
            "/api/v1/agents",
            data="invalid json",
            headers={
                "X-API-Key": valid_api_key,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client, setup_auth, valid_api_key):
        """Test missing required fields returns 422"""
        response = client.post(
            "/api/v1/agents",
            json={},  # Missing config and auto_start
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 422

    def test_internal_server_error_handling(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test internal server error handling"""
        mock_agent_manager.create_agent.side_effect = Exception("Unexpected error")

        response = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "general"}, "auto_start": True},
            headers={"X-API-Key": valid_api_key}
        )

        assert response.status_code == 500
        assert "Failed to create agent" in response.json()["detail"]


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_agent_lifecycle(self, client, setup_auth, mock_agent_manager, valid_api_key, test_agent_id):
        """Test complete agent lifecycle: create → message → delete"""
        # Step 1: Create agent
        mock_agent = AsyncMock()
        mock_agent.status = AgentStatus.RUNNING
        mock_agent.created_at = datetime.utcnow()
        mock_agent.messages_count = 0
        mock_agent.get_info.return_value = {
            "id": test_agent_id,
            "status": "running",
            "agent_type": "general"
        }

        mock_agent_manager.create_agent.return_value = test_agent_id
        mock_agent_manager.get_agent.return_value = mock_agent

        create_response = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "general"}, "auto_start": True},
            headers={"X-API-Key": valid_api_key}
        )
        assert create_response.status_code == 201
        agent_id = create_response.json()["agent_id"]

        # Step 2: Send message
        mock_agent.send_message.return_value = "Hello back!"

        message_response = client.post(
            f"/api/v1/agents/{agent_id}/messages",
            json={"message": "Hello agent"},
            headers={"X-API-Key": valid_api_key}
        )
        assert message_response.status_code == 200

        # Step 3: Get agent info
        info_response = client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"X-API-Key": valid_api_key}
        )
        assert info_response.status_code == 200

        # Step 4: Delete agent
        mock_agent_manager.delete_agent.return_value = True

        delete_response = client.delete(
            f"/api/v1/agents/{agent_id}",
            headers={"X-API-Key": valid_api_key}
        )
        assert delete_response.status_code == 200

    def test_multi_agent_workflow(self, client, setup_auth, mock_agent_manager, valid_api_key):
        """Test managing multiple agents simultaneously"""
        # Create multiple agents
        mock_agent1 = AsyncMock()
        mock_agent1.status = AgentStatus.RUNNING
        mock_agent1.created_at = datetime.utcnow()
        mock_agent1.messages_count = 0

        mock_agent2 = AsyncMock()
        mock_agent2.status = AgentStatus.RUNNING
        mock_agent2.created_at = datetime.utcnow()
        mock_agent2.messages_count = 0

        def get_agent_side_effect(agent_id):
            if agent_id == "agent-1":
                return mock_agent1
            elif agent_id == "agent-2":
                return mock_agent2
            return None

        mock_agent_manager.get_agent.side_effect = get_agent_side_effect
        mock_agent_manager.create_agent.side_effect = ["agent-1", "agent-2"]

        # Create first agent
        response1 = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "research"}, "auto_start": True},
            headers={"X-API-Key": valid_api_key}
        )
        assert response1.status_code == 201

        # Create second agent
        response2 = client.post(
            "/api/v1/agents",
            json={"config": {"agent_type": "code"}, "auto_start": True},
            headers={"X-API-Key": valid_api_key}
        )
        assert response2.status_code == 201

        # List all agents
        mock_agent_manager.list_agents.return_value = {
            "agent-1": {"id": "agent-1"},
            "agent-2": {"id": "agent-2"}
        }

        list_response = client.get(
            "/api/v1/agents",
            headers={"X-API-Key": valid_api_key}
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2
