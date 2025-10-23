# Quick Start Guide

Get started with Agent as a Service (AaaS) in minutes!

## Prerequisites

- Python 3.10 or higher
- Claude Code CLI installed and configured
- Anthropic API key

## Installation

### 1. Install Claude Code

First, install Claude Code CLI if you haven't already:

```bash
# Install Claude Code (follow official Anthropic instructions)
# https://docs.claude.com
```

### 2. Clone and Install AaaS

```bash
# Clone the repository
git clone https://github.com/wilbtc/agent-as-service.git
cd agent-as-service

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
ANTHROPIC_API_KEY=your-api-key-here
```

## Starting the Server

### Option 1: Using the CLI

```bash
aaas serve --host 0.0.0.0 --port 8000
```

### Option 2: Using Python

```python
from aaas.server import run_server

run_server(host="0.0.0.0", port=8000, reload=True)
```

### Option 3: Using Uvicorn Directly

```bash
uvicorn aaas.api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## Your First Agent

### Using Python Client

```python
from aaas import AgentClient

# Connect to the AaaS server
client = AgentClient(base_url="http://localhost:8000")

# Deploy an agent
agent = client.deploy_agent(
    template="general-assistant",
    config={
        "language": "en",
        "personality": "helpful"
    }
)

print(f"Agent deployed: {agent.id}")

# Send a message
response = agent.send("What can you help me with?")
print(f"Response: {response}")

# Cleanup
agent.delete()
client.close()
```

### Using CLI

```bash
# Deploy an agent
aaas deploy general-assistant

# List agents
aaas list

# Send a message
aaas send <agent-id> "Hello, how can you help me?"

# Delete an agent
aaas delete <agent-id>
```

### Using cURL

```bash
# Create an agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "template": "general-assistant",
      "language": "en"
    },
    "auto_start": true
  }'

# Send a message (replace {agent_id} with actual ID)
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs:** http://localhost:8000/docs
- **Alternative docs:** http://localhost:8000/redoc

## Common Tasks

### Deploy Multiple Agents

```python
from aaas import AgentClient

client = AgentClient()

# Deploy different types of agents
agents = {
    "support": client.deploy_agent("customer-service-pro"),
    "analyst": client.deploy_agent("data-analysis"),
    "writer": client.deploy_agent("content-creation"),
}

# Use them
response = agents["support"].send("I need help!")
print(response)
```

### Monitor Agent Status

```python
# Get all agents
agents = client.list_agents()

for agent_id, info in agents.items():
    print(f"Agent: {agent_id}")
    print(f"  Status: {info.status}")
    print(f"  Messages: {info.messages_count}")
    print(f"  PID: {info.pid}")
```

### Handle Errors

```python
try:
    agent = client.deploy_agent("my-template")
    response = agent.send("Hello")
except Exception as e:
    print(f"Error: {e}")
```

## Next Steps

- Read the [API Documentation](API.md)
- Check out [Examples](../examples/)
- Review [Configuration Options](CONFIGURATION.md)
- Learn about [Deployment](DEPLOYMENT.md)

## Troubleshooting

### Agent fails to start

1. Check that Claude Code is installed: `claude --version`
2. Verify your API key is set in `.env`
3. Check logs in `./logs/` directory

### Connection refused

1. Ensure the server is running: `curl http://localhost:8000/health`
2. Check the port isn't already in use
3. Verify firewall settings

### Agent timeout

1. Increase `AGENT_TIMEOUT` in `.env`
2. Check Claude Code subprocess is responsive
3. Review agent logs

## Support

For issues and questions:
- Telegram: [@wilbtc](https://t.me/wilbtc)
- GitHub Issues: [agent-as-service/issues](https://github.com/wilbtc/agent-as-service/issues)
