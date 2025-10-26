# Adaptive MCP Server Provisioning

## Overview

The Agent as a Service platform now supports **adaptive MCP (Model Context Protocol) server provisioning**. This feature automatically provisions the appropriate MCP servers for each agent type, providing enhanced capabilities while optimizing resource usage through intelligent sharing and lifecycle management.

## What are MCP Servers?

MCP servers extend Claude agents with additional tools and capabilities:
- **Filesystem** - File operations and management
- **Memory** - Persistent storage across conversations
- **Git/GitHub** - Version control integration
- **Web Search** - Internet search capabilities (Brave Search)
- **Browser** - Web browsing (Puppeteer)
- **Database** - PostgreSQL and SQLite integration
- **Slack** - Team communication
- **Google Drive** - Document access
- **Sequential Thinking** - Enhanced reasoning capabilities

## Key Features

### 1. **Adaptive Provisioning**
- Automatically provisions MCP servers based on agent type
- Each agent type gets the servers it needs
- No manual configuration required

### 2. **Resource Pooling**
- Shared servers can be used by multiple agents simultaneously
- Reduces resource overhead
- Smart connection management with max connection limits

### 3. **Lifecycle Management**
- Servers start on-demand when first needed
- Automatic health monitoring
- Idle timeout for unused servers
- Clean shutdown when agents are deleted

### 4. **Environment-Aware**
- Optional servers gracefully skip if environment variables missing
- Required servers fail appropriately
- Validates API keys and credentials

## Agent Type → MCP Server Mapping

### General Purpose Agent
- Filesystem
- Memory
- Sequential Thinking

### Research Agent
- Filesystem
- Memory
- Brave Search (web search)
- Puppeteer (browser automation)
- Sequential Thinking
- Git

### Code Agent
- Filesystem
- Memory
- Git
- GitHub (requires `GITHUB_PERSONAL_ACCESS_TOKEN`)
- Sequential Thinking

### Finance Agent
- Filesystem
- Memory
- Brave Search
- PostgreSQL (requires `POSTGRES_CONNECTION_STRING`)
- Sequential Thinking

### Customer Support Agent
- Filesystem
- Memory
- Slack (requires `SLACK_BOT_TOKEN`)
- Sequential Thinking

### Personal Assistant Agent
- Filesystem
- Memory
- Google Drive
- Sequential Thinking
- Brave Search

### Data Analysis Agent
- Filesystem
- Memory
- PostgreSQL
- SQLite
- Sequential Thinking

## ⚠️ Current Status

**MCP server provisioning is currently DISABLED by default** as subprocess management is not yet fully implemented (see `docs/MCP_2025_COMPLIANCE_AUDIT.md` for details).

To enable MCP servers:
```bash
export AAAS_ENABLE_MCP_SERVERS=true
```

**Note**: The architecture and API are complete, but actual MCP server processes don't start yet. This will be implemented in Phase 1 of the compliance roadmap.

## Configuration

### Enabling MCP Servers

Set in `.env` or environment:
```bash
AAAS_ENABLE_MCP_SERVERS=true
```

### Environment Variables

Set these environment variables to enable optional MCP servers:

```bash
# GitHub integration (Code agents)
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxx"

# Web search (Research, Finance, Personal Assistant agents)
export BRAVE_API_KEY="BSAxxxxx"

# Team communication (Customer Support agents)
export SLACK_BOT_TOKEN="xoxb-xxxxx"
export SLACK_TEAM_ID="T0xxxxx"

# Database access (Finance, Data Analysis agents)
export POSTGRES_CONNECTION_STRING="postgresql://user:pass@localhost/db"
```

### Settings Configuration

In `.env` or configuration file:

```python
# Enable/disable adaptive MCP provisioning
ENABLE_MCP_SERVERS=true

# MCP server idle timeout (seconds)
MCP_SERVER_IDLE_TIMEOUT=300

# MCP server health check interval (seconds)
MCP_SERVER_HEALTH_CHECK_INTERVAL=60
```

## API Endpoints

### List All MCP Servers
```bash
GET /api/v1/mcp-servers
```

Response:
```json
{
  "servers": {
    "uuid-1": {
      "server_id": "uuid-1",
      "server_type": "filesystem",
      "status": "running",
      "connected_agents": ["agent-1", "agent-2"],
      "connection_count": 2,
      "created_at": "2025-10-25T23:00:00Z"
    }
  },
  "count": 1
}
```

### Get MCP Servers for Agent
```bash
GET /api/v1/agents/{agent_id}/mcp-servers
```

Response:
```json
{
  "agent_id": "agent-uuid",
  "servers": [
    {
      "server_id": "uuid-1",
      "server_type": "filesystem",
      "status": "running",
      "endpoint": "stdio://filesystem"
    },
    {
      "server_id": "uuid-2",
      "server_type": "memory",
      "status": "running",
      "endpoint": "stdio://memory"
    }
  ],
  "count": 2
}
```

### List Available MCP Server Types
```bash
GET /api/v1/mcp-server-types
```

Response:
```json
{
  "server_types": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "shared": true,
      "max_connections": 50,
      "required_env_vars": [],
      "optional": false
    }
  },
  "agent_requirements": {
    "research": ["filesystem", "memory", "brave_search", "puppeteer", "sequential_thinking", "git"]
  }
}
```

## Usage Examples

### Create a Research Agent with MCP Servers

```python
import requests

# Create research agent
response = requests.post(
    "http://localhost:8000/api/v1/agents",
    json={
        "config": {
            "agent_type": "research"
        },
        "auto_start": true
    },
    headers={"X-API-Key": "your-api-key"}
)

agent_id = response.json()["agent_id"]

# MCP servers automatically provisioned:
# - filesystem (shared)
# - memory (shared)
# - brave_search (shared, if BRAVE_API_KEY set)
# - puppeteer (dedicated instance)
# - sequential_thinking (shared)
# - git (shared)

# Check which servers are connected
mcp_response = requests.get(
    f"http://localhost:8000/api/v1/agents/{agent_id}/mcp-servers",
    headers={"X-API-Key": "your-api-key"}
)

print(f"Agent has {mcp_response.json()['count']} MCP servers")
```

### Monitor MCP Server Health

```python
# List all running MCP servers
servers_response = requests.get(
    "http://localhost:8000/api/v1/mcp-servers",
    headers={"X-API-Key": "your-api-key"}
)

for server_id, server_info in servers_response.json()["servers"].items():
    print(f"{server_info['server_type']}: {server_info['status']}")
    print(f"  Connected agents: {server_info['connection_count']}")
    print(f"  Last health check: {server_info['last_health_check']}")
```

## Architecture

### Resource Pooling

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Agent 1   │    │   Agent 2   │    │   Agent 3   │
│  (Research) │    │  (Research) │    │    (Code)   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                   │
       ├──────────────────┴───────────────────┤
       │         Shared MCP Servers            │
       ├──────────────────┬───────────────────┤
       │                  │                   │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
│ Filesystem  │    │   Memory    │    │     Git     │
│  (50 conn)  │    │  (100 conn) │    │  (20 conn)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Lifecycle Flow

```
1. Agent Created → MCP Manager provisions required servers
2. Server Shared? → Reuse existing OR create new
3. Health Check → Periodic monitoring (60s interval)
4. Agent Deleted → Disconnect from servers
5. Server Idle? → Shutdown after timeout (300s)
```

## Performance Considerations

### Resource Optimization
- **Shared servers**: Filesystem, Memory, Git support 20-100 concurrent connections
- **Dedicated servers**: Puppeteer gets one instance per agent
- **Idle cleanup**: Unused servers shut down after 5 minutes
- **Health monitoring**: Failed servers trigger automatic recovery

### Scalability
- MCP servers scale independently of agents
- Connection pooling prevents resource exhaustion
- Graceful degradation for optional servers

## Troubleshooting

### Common Issues

**Problem**: Research agent missing web search capability
```bash
# Solution: Set Brave API key
export BRAVE_API_KEY="your-brave-api-key"
```

**Problem**: Code agent can't access GitHub
```bash
# Solution: Set GitHub token
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxx"
```

**Problem**: MCP server health check failures
```bash
# Check server logs
GET /api/v1/mcp-servers

# Look for error_message in server info
# Common causes:
# - Missing Node.js/npm
# - Network connectivity
# - Invalid credentials
```

### Logging

Enable debug logging for MCP operations:
```python
import logging
logging.getLogger("aaas.mcp_manager").setLevel(logging.DEBUG)
```

## Future Enhancements

- [ ] Custom MCP server registration
- [ ] Dynamic server scaling based on load
- [ ] MCP server metrics and analytics
- [ ] Server-side rate limiting
- [ ] MCP server versioning and updates
- [ ] Multi-region MCP server deployment

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Building Custom MCP Servers](https://modelcontextprotocol.io/docs/guides/building-mcp-servers)
