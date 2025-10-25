# Agent as a Service (AaaS)

<div align="center">

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/wilbtc/agent-as-service)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Claude SDK](https://img.shields.io/badge/Claude%20Agent%20SDK-latest-purple)](https://docs.anthropic.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

**A RESTful API platform for deploying and managing Claude AI agents at scale**

[Quick Start](#-quick-start) • [Documentation](#-documentation) • [API Reference](#-api-reference) • [Examples](#-examples) • [Contact](#-contact)

---

### ⚠️ PROPRIETARY SOFTWARE NOTICE

**This is closed-source, proprietary software owned by WilBtc.**

- 🔒 **Licensed Use Only** - Authorization required for all use
- 💼 **Commercial Software** - Contact for licensing terms
- ❌ **Not Open Source** - No unauthorized copying or distribution
- 📞 **Get Access**: [@wilbtc on Telegram](https://t.me/wilbtc)

</div>

---

## 🎯 Overview

Agent as a Service (AaaS) is a production-ready platform that provides a RESTful API for deploying, managing, and orchestrating multiple Claude AI agents. Built on the official Claude Agent SDK and FastAPI, it enables developers to integrate powerful AI agents into their applications with minimal setup.

### What is AaaS?

AaaS wraps the Claude Agent SDK in a scalable web service, providing:

- **RESTful API** for agent lifecycle management (create, start, stop, delete)
- **Multi-agent orchestration** with isolated subprocess management
- **8 specialized agent types** optimized for different use cases
- **Async operations** for high-performance concurrent agent handling
- **Security features** including API key authentication and rate limiting
- **Simple Python client** for rapid integration

## ✨ Key Features

### 🤖 Specialized Agent Types

AaaS provides 8 pre-configured agent types, each optimized for specific tasks:

| Agent Type | Description | Use Cases |
|------------|-------------|-----------|
| **General** | General-purpose agent for diverse tasks | Chat, Q&A, general assistance |
| **Research** | Web search and research capabilities | Market research, data gathering |
| **Code** | Software development and debugging | Code review, debugging, refactoring |
| **Finance** | Financial analysis and calculations | Portfolio analysis, risk assessment |
| **Customer Support** | Customer service interactions | Support tickets, FAQ responses |
| **Personal Assistant** | Scheduling and task management | Calendar management, reminders |
| **Data Analysis** | Data processing and insights | Report generation, statistics |
| **Custom** | Fully customizable agent | Domain-specific applications |

### 🔒 Security & Performance

- **API Key Authentication** - Secure access control for production environments
- **Rate Limiting** - Configurable request throttling with slowapi
- **Isolated Subprocesses** - Each agent runs in its own Claude Code subprocess
- **Resource Management** - Configurable max agents and timeout limits
- **Tool Access Control** - Granular permission system for agent capabilities
- **Async Architecture** - Non-blocking operations for optimal performance

### 🚀 Developer Experience

- **RESTful API** - Standard HTTP endpoints with OpenAPI documentation
- **Python Client** - High-level client library for easy integration
- **Hot Reload** - Development server with auto-reload on code changes
- **Interactive Docs** - Built-in Swagger UI at `/docs`
- **Comprehensive Tests** - 100+ tests covering all major features
- **Docker Support** - Containerized deployment ready

## 📋 Requirements

- Python 3.10 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- 2GB+ RAM recommended
- Linux, macOS, or Windows

## 🚀 Quick Start

> **⚠️ IMPORTANT**: This is proprietary software. Access is restricted to authorized users only.
> Contact [@wilbtc](https://t.me/wilbtc) for licensing and access.

### Option 1: Hosted Service (Recommended)

For authorized customers, use our managed AaaS instance:

```bash
# Install client library (requires authorized access)
pip install aaas-client
```

```python
from aaas import AgentClient, AgentType

# Connect to hosted service
client = AgentClient(
    base_url="https://api.aaas.example.com",
    api_key="your-api-key"  # Provided upon licensing
)

# Create and use a research agent
agent_id = client.create_agent(agent_type=AgentType.RESEARCH)
response = client.send_message(agent_id, "Research the latest AI trends")
print(response)

# Cleanup
client.delete_agent(agent_id)
```

**Get Licensed Access**: [Contact @wilbtc](https://t.me/wilbtc) for pricing and licensing

📚 **[View Hosted Service Guide →](docs/HOSTED_SERVICE.md)**

---

### Option 2: Licensed Self-Hosted Deployment

For authorized licensees deploying on their own infrastructure:

#### 1. Installation

> **Note**: Repository access requires a valid license. Contact [@wilbtc](https://t.me/wilbtc) for licensing.

```bash
# Clone the repository (requires authorized access)
git clone https://github.com/wilbtc/agent-as-service.git
cd agent-as-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

#### 2. Configuration

Create a `.env` file with your settings:

```bash
# Required: Anthropic API Key
ANTHROPIC_API_KEY=your-api-key-here

# Optional: API Configuration
API_KEY=your-aaas-api-key        # Enable API authentication
REQUIRE_API_KEY=true             # Enforce authentication
HOST=0.0.0.0
PORT=8000

# Optional: Agent Configuration
MAX_AGENTS=50                     # Maximum concurrent agents
AGENT_TIMEOUT=3600               # Agent timeout in seconds
MAX_TURNS=25                     # Max conversation turns per agent

# Optional: Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_AGENT_CREATION=10
```

#### 3. Start the Server

```bash
# Development mode (with auto-reload)
uvicorn aaas.api:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn aaas.api:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start at `http://localhost:8000`

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📖 Usage Examples

### Using the REST API

#### Create an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "config": {
      "agent_type": "research",
      "personality": "analytical",
      "language": "en"
    },
    "auto_start": true
  }'
```

Response:
```json
{
  "agent_id": "agent-abc123",
  "status": "running",
  "config": {
    "agent_type": "research",
    "personality": "analytical"
  }
}
```

#### Send a Message

```bash
curl -X POST http://localhost:8000/api/v1/agents/agent-abc123/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "Research the latest developments in quantum computing",
    "context": {
      "user_id": "user-123",
      "session_id": "session-456"
    }
  }'
```

#### List All Agents

```bash
curl http://localhost:8000/api/v1/agents \
  -H "X-API-Key: your-api-key"
```

#### Delete an Agent

```bash
curl -X DELETE http://localhost:8000/api/v1/agents/agent-abc123 \
  -H "X-API-Key: your-api-key"
```

### Using the Python Client

```python
from aaas import AgentClient, AgentConfig, AgentType, PermissionMode

# Initialize client
client = AgentClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Create a code analysis agent
config = AgentConfig(
    agent_type=AgentType.CODE,
    personality="precise",
    permission_mode=PermissionMode.ACCEPT_EDITS,
    max_tokens=8192
)

agent_id = client.create_agent(config, auto_start=True)
print(f"Created agent: {agent_id}")

# Send a message
response = client.send_message(
    agent_id,
    "Review this Python function for security issues: def process_user_input(data): return eval(data)"
)
print(f"Agent response: {response}")

# Get agent info
info = client.get_agent(agent_id)
print(f"Agent status: {info['status']}")
print(f"Messages sent: {info['messages_count']}")

# Cleanup
client.delete_agent(agent_id)
```

### Quick Query (One-Shot Requests)

For simple, stateless queries without maintaining an agent:

```python
# Quick query without creating a persistent agent
response = client.quick_query(
    message="Explain quantum entanglement in simple terms",
    agent_type=AgentType.RESEARCH
)
print(response)
```

## 🏗️ Architecture

### System Design

```
┌──────────────┐      HTTP/REST      ┌─────────────┐      AsyncIO      ┌──────────────────┐
│   Client     │────────────────────▶│  FastAPI    │─────────────────▶│ Agent Manager    │
│   Library    │                     │  Web Server │                   │   (Orchestrator) │
└──────────────┘                     └─────────────┘                   └──────────────────┘
                                                                                 │
                                                                                 │ Manages
                                                                                 ▼
                                                                    ┌─────────────────────────┐
                                                                    │   Agent Subprocesses    │
                                                                    │  ┌─────┐  ┌─────┐       │
                                                                    │  │ AG1 │  │ AG2 │  ...  │
                                                                    │  └─────┘  └─────┘       │
                                                                    │   (Claude Code SDK)     │
                                                                    └─────────────────────────┘
```

### Core Components

1. **FastAPI Web Server** (`api.py`)
   - RESTful API endpoints
   - Request validation with Pydantic
   - Authentication and rate limiting
   - OpenAPI documentation

2. **Agent Manager** (`agent_manager.py`)
   - Lifecycle management (create, start, stop, delete)
   - Subprocess orchestration
   - Message routing
   - Resource pooling

3. **Agent Classes** (`agent_manager.py`)
   - Individual agent instances
   - Claude SDK integration
   - State management
   - Message handling

4. **Python Client** (`client.py`)
   - High-level API wrapper
   - Automatic error handling
   - Connection management
   - Type hints for IDE support

### Project Structure

```
agent-as-service/
├── src/aaas/
│   ├── __init__.py           # Package exports
│   ├── agent_manager.py      # Agent orchestration and subprocess management
│   ├── api.py               # FastAPI REST API endpoints
│   ├── auth.py              # Authentication middleware
│   ├── client.py            # Python client library
│   ├── config.py            # Configuration and settings
│   ├── models.py            # Pydantic models and enums
│   └── server.py            # Server startup utilities
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_agent_types.py  # Agent type tests
│   ├── test_api_endpoints.py # API endpoint tests
│   ├── test_agent_manager.py # Agent manager tests
│   └── README.md            # Testing documentation
├── docs/
│   └── HOSTED_SERVICE.md    # Hosted service guide
├── examples/
│   └── hosted_service_example.py
├── .env.example             # Example environment configuration
├── pytest.ini              # Test configuration
├── pyproject.toml          # Project metadata and dependencies
├── Dockerfile              # Docker container definition
└── README.md               # This file
```

## 🧪 Testing

AaaS includes a comprehensive test suite with 100+ tests:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
pytest

# Run with coverage report
pytest --cov=src/aaas --cov-report=html

# Run specific test categories
pytest -m api           # API endpoint tests
pytest -m auth          # Authentication tests
pytest -m unit          # Unit tests
```

Test coverage includes:
- ✅ All 8 agent types and configurations
- ✅ API endpoints with authentication
- ✅ Rate limiting enforcement
- ✅ Agent lifecycle operations
- ✅ Error handling
- ✅ Concurrent operations

See [tests/README.md](tests/README.md) for detailed testing documentation.

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t aaas:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e API_KEY=your-aaas-key \
  -e REQUIRE_API_KEY=true \
  --name aaas-server \
  aaas:latest
```

## 📚 Documentation

### API Reference

Full API documentation is available at `/docs` when the server is running:
- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with service info |
| `GET` | `/health` | Health check and status |
| `POST` | `/api/v1/agents` | Create a new agent |
| `GET` | `/api/v1/agents` | List all agents |
| `GET` | `/api/v1/agents/{id}` | Get agent details |
| `POST` | `/api/v1/agents/{id}/start` | Start an agent |
| `POST` | `/api/v1/agents/{id}/stop` | Stop an agent |
| `DELETE` | `/api/v1/agents/{id}` | Delete an agent |
| `POST` | `/api/v1/agents/{id}/messages` | Send message to agent |
| `GET` | `/api/v1/agent-types` | List available agent types |
| `POST` | `/api/v1/query` | Quick query (stateless) |

### Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ANTHROPIC_API_KEY` | Required | Your Anthropic API key |
| `API_KEY` | None | AaaS API key for authentication |
| `REQUIRE_API_KEY` | `false` | Enable API key requirement |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `MAX_AGENTS` | `50` | Maximum concurrent agents |
| `AGENT_TIMEOUT` | `3600` | Agent timeout (seconds) |
| `MAX_TURNS` | `25` | Max conversation turns |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | `60` | Default rate limit |
| `LOG_LEVEL` | `INFO` | Logging level |

See `.env.example` for complete configuration options.

## 💡 Examples

Check the `examples/` directory for more detailed usage examples:

- `hosted_service_example.py` - Complete hosted service integration
- Coming soon: Multi-agent workflows, streaming responses, webhooks

## 🛠️ Development

> **For Authorized Developers Only**: Development access requires a valid license agreement.

### Setup Development Environment

```bash
# Clone repository (authorized access required)
git clone https://github.com/wilbtc/agent-as-service.git
cd agent-as-service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Start dev server with auto-reload
uvicorn aaas.api:app --reload
```

### Contributing

This is proprietary software. Contributions are accepted only from:
- Licensed customers
- Authorized development partners
- WilBtc team members

For collaboration inquiries, contact [@wilbtc](https://t.me/wilbtc)

## 🔒 Security

### Authentication

Enable API key authentication for production:

```bash
# Generate a secure API key
export API_KEY=$(openssl rand -hex 32)
export REQUIRE_API_KEY=true
```

All requests must include the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/agents
```

### Rate Limiting

Configure rate limits to prevent abuse:

```bash
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_PER_MINUTE=60
export RATE_LIMIT_AGENT_CREATION=10  # Stricter limit for agent creation
```

### Best Practices

- ✅ Use HTTPS in production
- ✅ Enable API key authentication
- ✅ Configure appropriate rate limits
- ✅ Set resource limits (max agents, timeouts)
- ✅ Monitor agent usage and costs
- ✅ Regularly update dependencies

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
# Ensure package is installed
pip install -e .
```

**"Anthropic API key not set"**
```bash
# Set your API key
export ANTHROPIC_API_KEY=your-key-here
```

**Port already in use**
```bash
# Use a different port
uvicorn aaas.api:app --port 8080
```

**Agent creation fails**
```bash
# Check logs for details
# Verify API key is valid
# Ensure sufficient system resources
```

## 📊 Performance

AaaS is designed for production workloads:

- **Agent Creation**: ~2-3 seconds per agent
- **Message Processing**: Sub-second response times (depends on Claude API)
- **Concurrent Agents**: Tested with 50+ concurrent agents
- **Memory Usage**: ~100MB base + ~50MB per active agent
- **Async Operations**: Non-blocking I/O for optimal throughput

## 🗺️ Roadmap

### Version 2.1 (Next)
- [ ] WebSocket support for streaming responses
- [ ] Webhook callbacks for async notifications
- [ ] Agent templates and presets
- [ ] Metrics and monitoring dashboard
- [ ] Database persistence for agent state

### Version 2.2
- [ ] Multi-tenancy support
- [ ] Usage analytics and billing
- [ ] Custom tool integration
- [ ] Agent collaboration features

### Version 3.0
- [ ] Kubernetes deployment manifests
- [ ] Distributed agent orchestration
- [ ] Advanced security features
- [ ] Plugin system for extensions

## 📞 Contact

**Developer**: WilBtc
**Telegram**: [@wilbtc](https://t.me/wilbtc)

For:
- 💼 Hosted service access
- 🤝 Partnership opportunities
- 🐛 Bug reports and feature requests
- 💡 Custom development inquiries

## 📄 License

**Proprietary Software - All Rights Reserved**

Copyright © 2025 WilBtc

This is proprietary, closed-source software. All rights reserved.

**Restrictions:**
- ❌ No unauthorized use, copying, or distribution
- ❌ No modification or derivative works without license
- ❌ No reverse engineering or decompilation
- ❌ No public redistribution or sharing
- ✅ Use permitted only under valid license agreement

**To obtain a license:**
- Contact [@wilbtc](https://t.me/wilbtc) for licensing terms
- Commercial licenses available
- Custom enterprise agreements available

Unauthorized use is strictly prohibited and may result in legal action.

## 🙏 Acknowledgments

Built with:
- [Claude Agent SDK](https://docs.anthropic.com/) by Anthropic
- [FastAPI](https://fastapi.tiangolo.com/) by Sebastián Ramírez
- [Pydantic](https://docs.pydantic.dev/) for data validation
- [slowapi](https://github.com/laurentS/slowapi) for rate limiting

---

<div align="center">

**Agent as a Service (AaaS)**
*Professional AI Agent Orchestration*

**© 2025 WilBtc. All Rights Reserved.**

**Proprietary Software - Licensed Use Only**

---

**Contact for Licensing**: [@wilbtc](https://t.me/wilbtc)

Unauthorized use, reproduction, or distribution is strictly prohibited.

</div>
