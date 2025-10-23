# AaaS API Documentation

## Overview

The Agent as a Service (AaaS) REST API provides endpoints for managing Claude Code agent instances.

**Base URL:** `http://localhost:8000`
**API Version:** v1
**API Prefix:** `/api/v1`

## Authentication

All API requests require an API key passed in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/agents
```

## Endpoints

### Health Check

#### `GET /health`

Check the service health status.

**Response:**
```json
{
  "status": "healthy",
  "agents_count": 5,
  "max_agents": 100
}
```

---

### Create Agent

#### `POST /api/v1/agents`

Create a new agent instance.

**Request Body:**
```json
{
  "config": {
    "template": "customer-service-pro",
    "language": "en",
    "personality": "professional",
    "integration": "zendesk",
    "max_tokens": 4096,
    "temperature": 1.0,
    "working_directory": null,
    "environment": {}
  },
  "auto_start": true
}
```

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "endpoint": "/api/v1/agents/123e4567-e89b-12d3-a456-426614174000",
  "message": "Agent created successfully with ID: 123e4567-e89b-12d3-a456-426614174000"
}
```

---

### List Agents

#### `GET /api/v1/agents`

List all agent instances.

**Response:**
```json
{
  "123e4567-e89b-12d3-a456-426614174000": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "running",
    "config": {
      "template": "customer-service-pro",
      "language": "en",
      "personality": "professional"
    },
    "created_at": "2025-10-23T10:00:00Z",
    "endpoint": "/api/v1/agents/123e4567-e89b-12d3-a456-426614174000",
    "pid": 12345,
    "messages_count": 42
  }
}
```

---

### Get Agent

#### `GET /api/v1/agents/{agent_id}`

Get information about a specific agent.

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "config": {
    "template": "customer-service-pro",
    "language": "en",
    "personality": "professional"
  },
  "created_at": "2025-10-23T10:00:00Z",
  "endpoint": "/api/v1/agents/123e4567-e89b-12d3-a456-426614174000",
  "pid": 12345,
  "messages_count": 42
}
```

---

### Send Message

#### `POST /api/v1/agents/{agent_id}/messages`

Send a message to an agent.

**Request Body:**
```json
{
  "message": "Hello, I need help with my order",
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Response:**
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "response": "I'd be happy to help you with your order. Could you please provide your order number?",
  "timestamp": "2025-10-23T10:00:00Z",
  "metadata": {
    "messages_count": 43
  }
}
```

---

### Start Agent

#### `POST /api/v1/agents/{agent_id}/start`

Start a stopped agent.

**Response:**
```json
{
  "status": "success",
  "message": "Agent 123e4567-e89b-12d3-a456-426614174000 started"
}
```

---

### Stop Agent

#### `POST /api/v1/agents/{agent_id}/stop`

Stop a running agent.

**Response:**
```json
{
  "status": "success",
  "message": "Agent 123e4567-e89b-12d3-a456-426614174000 stopped"
}
```

---

### Delete Agent

#### `DELETE /api/v1/agents/{agent_id}`

Delete an agent instance.

**Response:**
```json
{
  "status": "success",
  "message": "Agent 123e4567-e89b-12d3-a456-426614174000 deleted"
}
```

---

## Agent Status

Agents can have the following statuses:

- `starting` - Agent is being initialized
- `running` - Agent is active and ready to process messages
- `stopped` - Agent has been stopped
- `error` - Agent encountered an error
- `terminated` - Agent process has terminated

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:

- `400` - Bad Request
- `404` - Agent Not Found
- `500` - Internal Server Error

## Rate Limiting

The API currently does not implement rate limiting, but this may be added in future versions.

## Examples

### Using cURL

```bash
# Create an agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "template": "customer-service-pro",
      "language": "en"
    },
    "auto_start": true
  }'

# Send a message
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me?"
  }'

# Delete an agent
curl -X DELETE http://localhost:8000/api/v1/agents/{agent_id}
```

### Using Python

```python
import requests

# Create an agent
response = requests.post(
    "http://localhost:8000/api/v1/agents",
    json={
        "config": {
            "template": "customer-service-pro",
            "language": "en"
        },
        "auto_start": True
    }
)
agent_data = response.json()
agent_id = agent_data["agent_id"]

# Send a message
response = requests.post(
    f"http://localhost:8000/api/v1/agents/{agent_id}/messages",
    json={"message": "Hello!"}
)
print(response.json()["response"])
```
