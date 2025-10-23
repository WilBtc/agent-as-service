"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from aaas.api import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Agent as a Service"
    assert "version" in data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "agents_count" in data
    assert "max_agents" in data


def test_create_agent(client):
    """Test creating an agent"""
    payload = {
        "config": {
            "template": "test-agent",
            "language": "en"
        },
        "auto_start": False
    }

    response = client.post("/api/v1/agents", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "agent_id" in data
    assert data["status"] in ["stopped", "starting", "running"]
    assert "endpoint" in data


def test_list_agents(client):
    """Test listing agents"""
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_nonexistent_agent(client):
    """Test getting a non-existent agent"""
    response = client.get("/api/v1/agents/nonexistent-id")
    assert response.status_code == 404


def test_delete_nonexistent_agent(client):
    """Test deleting a non-existent agent"""
    response = client.delete("/api/v1/agents/nonexistent-id")
    assert response.status_code == 404


def test_create_and_delete_agent(client):
    """Test creating and then deleting an agent"""
    # Create agent
    payload = {
        "config": {
            "template": "test-agent",
            "language": "en"
        },
        "auto_start": False
    }

    create_response = client.post("/api/v1/agents", json=payload)
    assert create_response.status_code == 201
    agent_id = create_response.json()["agent_id"]

    # Get agent
    get_response = client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == 200

    # Delete agent
    delete_response = client.delete(f"/api/v1/agents/{agent_id}")
    assert delete_response.status_code == 200

    # Verify deletion
    verify_response = client.get(f"/api/v1/agents/{agent_id}")
    assert verify_response.status_code == 404
