# Changelog

All notable changes to Agent as a Service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-25

### 🚀 Major Update: Claude Agent SDK Integration & Specialized Agent Types

This is a major upgrade that modernizes the platform to use the official Claude Agent SDK and introduces intelligent agent type selection.

#### Added - Claude Agent SDK Integration

- **Claude Agent SDK** - Complete migration from raw subprocess management to the official Claude Agent SDK
  - Uses Claude Code subprocess under the hood with a robust, maintained interface
  - Better error handling and lifecycle management
  - Built-in context management and automatic compaction
  - Rich tool ecosystem support (Read, Write, Bash, Grep, Glob, WebSearch, WebFetch, etc.)
  - Advanced permission modes (Ask, AcceptEdits, AcceptAll)

#### Added - Specialized Agent Types

- **8 Built-in Agent Types** with optimized configurations:
  - `GENERAL` - General-purpose agent for various tasks
  - `RESEARCH` - Deep research and comprehensive analysis
  - `CODE` - Code development, review, and debugging
  - `FINANCE` - Financial analysis and portfolio management
  - `CUSTOMER_SUPPORT` - Customer service and support tasks
  - `PERSONAL_ASSISTANT` - Productivity and task management
  - `DATA_ANALYSIS` - Data analysis and insights
  - `CUSTOM` - User-defined custom configuration

- **Agent Type Configurations** - Each type includes:
  - Specialized system prompts
  - Optimized tool access lists
  - Default permission modes
  - Personality and behavior settings

#### Added - New API Endpoints

- **`GET /api/v1/agent-types`** - List all available agent types with descriptions
- **`POST /api/v1/query`** - Quick query endpoint for one-off agent interactions
  - Supports all agent types
  - No agent lifecycle management needed
  - Perfect for simple queries

#### Enhanced - Agent Configuration

- **`AgentType` enum** - Type-safe agent type selection
- **`PermissionMode` enum** - Control agent operation permissions
- **Enhanced `AgentConfig` model** with new fields:
  - `agent_type` - Select specialized agent type
  - `system_prompt` - Custom system prompts
  - `allowed_tools` - Fine-grained tool access control
  - `permission_mode` - Operation permission settings
  - `max_turns` - Conversation turn limits
  - `model` - Claude model selection

#### Enhanced - Python Client

- **Updated `AgentClient`** with new methods:
  - `list_agent_types()` - Discover available agent types
  - `quick_query()` - Send one-off queries without agent management
  - `deploy_agent()` - Now supports `agent_type` parameter
  - Backward compatible with existing `template` parameter

#### Enhanced - Agent Manager

- **`ClaudeAgent` class** - Replaces `ClaudeCodeAgent`
  - Uses Claude Agent SDK's `ClaudeSDKClient`
  - Better message handling and response extraction
  - Conversation history tracking
  - Improved error handling and logging

- **`AgentManager` enhancements**:
  - `query_agent()` - Quick query method for temporary agents
  - Smart template-to-type mapping for backward compatibility
  - Better agent lifecycle management

#### Updated - Examples

- **`basic_usage.py`** - Demonstrates new agent types and quick queries
- **`advanced_usage.py`** - Shows multiple specialized agents working together
  - Research, Code, Finance, and Data Analysis agents
  - Agent type comparison
  - Advanced configuration options

#### Updated - Documentation

- Enhanced CHANGELOG with comprehensive upgrade guide
- Updated code comments to clarify Claude Code subprocess usage
- Added examples of specialized agent configurations

#### Technical Improvements

- **Better Subprocess Management** - Claude Agent SDK handles:
  - Process lifecycle and cleanup
  - Message serialization and streaming
  - Context window management
  - Tool execution and permissions

- **Type Safety** - Added enums for:
  - Agent types
  - Permission modes
  - All validated with Pydantic

- **Smart Defaults** - Each agent type comes with:
  - Optimized system prompts
  - Appropriate tool access
  - Sensible permission defaults

### Changed

- **BREAKING**: `ClaudeCodeAgent` renamed to `ClaudeAgent`
- **BREAKING**: Agent creation now requires `agent_type` (defaults to GENERAL)
- `template` parameter is deprecated but still supported for backward compatibility
- Process ID (PID) no longer exposed as SDK abstracts subprocess details
- Updated all dependencies to support Claude Agent SDK

### Dependencies

- **Added**: `claude-agent-sdk>=0.1.0` - Official Claude Agent SDK
- **Added**: `anthropic>=0.39.0` - Anthropic API client
- **Updated**: `pydantic>=2.5.3` - For enhanced model validation

### Migration Guide from 1.0.0 to 2.0.0

**Prerequisites:**
- Claude Code 2.0.0+: `npm install -g @anthropic-ai/claude-code`
- Python 3.10 or higher
- Anthropic API key

**Installation:**
```bash
git pull origin main
pip install -e .  # Installs new dependencies including claude-agent-sdk
```

**Code Migration:**

Old way (still works):
```python
agent = client.deploy_agent(template="customer-service-pro")
```

New way (recommended):
```python
from aaas import AgentType
agent = client.deploy_agent(agent_type=AgentType.CUSTOMER_SUPPORT)
```

**Benefits:**
- More robust subprocess management
- Better error handling
- Specialized agent types
- Quick query support
- Future-proof with official SDK

## [1.0.0] - 2025-10-23

### Added - Complete Implementation

This is the initial implementation release, upgrading from a marketing repository to a fully functional agent service.

#### Core Features
- **Agent Management System**
  - `AgentManager` class for managing multiple Claude Code instances
  - `ClaudeCodeAgent` class for individual agent control
  - Full subprocess lifecycle management (start, stop, restart)
  - Isolated working directories per agent
  - Custom environment variable support per agent

#### API Server
- **FastAPI REST API** with the following endpoints:
  - `POST /api/v1/agents` - Create new agent
  - `GET /api/v1/agents` - List all agents
  - `GET /api/v1/agents/{id}` - Get agent information
  - `POST /api/v1/agents/{id}/messages` - Send message to agent
  - `POST /api/v1/agents/{id}/start` - Start agent
  - `POST /api/v1/agents/{id}/stop` - Stop agent
  - `DELETE /api/v1/agents/{id}` - Delete agent
  - `GET /health` - Health check endpoint
  - `GET /` - Service information

#### Client Library
- **Python Client** (`AgentClient`)
  - Easy-to-use SDK for programmatic access
  - Context manager support
  - Full API coverage
  - `DeployedAgent` class for agent operations

#### CLI Tool
- **Command-line interface** with commands:
  - `aaas serve` - Start the API server
  - `aaas deploy` - Deploy a new agent
  - `aaas list` - List all agents
  - `aaas send` - Send message to agent
  - `aaas delete` - Delete an agent

#### Configuration
- **Environment-based configuration** using `pydantic-settings`
- `.env.example` template provided
- Configurable parameters:
  - API host and port
  - Claude Code path and API key
  - Maximum agents limit
  - Agent timeout settings
  - Logging configuration

#### Documentation
- **Comprehensive documentation**:
  - `docs/QUICKSTART.md` - Quick start guide
  - `docs/API.md` - Complete API reference
  - `docs/DEPLOYMENT.md` - Production deployment guide
  - `docs/TECHNICAL.md` - Technical implementation details
  - `docs/FAQ.md` - Frequently asked questions
  - `docs/FEATURES.md` - Detailed feature list

#### Examples
- **Usage examples**:
  - `examples/basic_usage.py` - Basic agent deployment
  - `examples/advanced_usage.py` - Multiple agent management
  - `examples/api_server.py` - Server startup example

#### Testing
- **Test suite** using pytest:
  - `tests/test_agent_manager.py` - Agent manager tests
  - `tests/test_api.py` - API endpoint tests
  - Async test support with pytest-asyncio

#### Deployment
- **Docker support**:
  - `Dockerfile` for container builds
  - `docker-compose.yml` for easy deployment
  - Health checks configured
  - Production-ready setup

#### Project Structure
- **Well-organized codebase**:
  - `src/aaas/` - Main package
  - `tests/` - Test suite
  - `examples/` - Usage examples
  - `docs/` - Documentation
  - `pyproject.toml` - Modern Python packaging
  - `requirements.txt` - Dependency list

#### Data Models
- **Pydantic models** for type safety:
  - `AgentConfig` - Agent configuration
  - `AgentInfo` - Agent information
  - `AgentStatus` - Agent status enum
  - `AgentResponse` - Agent response
  - `MessageRequest` - Message request
  - `CreateAgentRequest` - Agent creation request
  - `CreateAgentResponse` - Agent creation response

#### Technical Features
- **Async/await** pattern throughout
- **Process isolation** for each agent
- **Graceful shutdown** handling
- **Error handling** at all levels
- **Structured logging** support
- **CORS support** for web integration
- **Health checks** for monitoring
- **Resource limits** enforcement

### Changed
- Updated README.md with implementation details
- Enhanced documentation with technical architecture
- Added practical usage examples

### Technical Details

#### Claude Code Integration
- Uses asyncio subprocess management
- Bidirectional communication via stdin/stdout
- Continuous output reader task
- Timeout support for operations
- Environment variable isolation

#### Performance
- Asynchronous I/O for concurrent operations
- Lock-based thread safety
- Configurable agent limits
- Resource monitoring support

#### Security
- API key authentication support
- CORS configuration
- Input validation via Pydantic
- Isolated working directories
- Process resource limits

## [0.1.0] - 2025-01-15

### Initial
- Marketing repository created
- Basic documentation structure
- README with feature overview
- License and contributing guidelines

---

## Upgrade Notes

### From 0.1.0 to 1.0.0

This is a major upgrade from a marketing repository to a fully functional implementation.

**Prerequisites:**
- Python 3.10 or higher
- Claude Code CLI installed
- Anthropic API key

**Installation:**
```bash
git pull origin main
pip install -e .
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

**Breaking Changes:**
- This is the first implementation release
- No backward compatibility concerns as previous version was documentation-only

**New Requirements:**
- FastAPI
- Uvicorn
- Pydantic
- httpx
- aiofiles

## Migration Guide

Since this is the first implementation, there's no migration needed. Simply:

1. Pull the latest code
2. Install dependencies: `pip install -e .`
3. Configure `.env` file
4. Start the server: `aaas serve`

For detailed setup instructions, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Support

For questions or issues:
- Telegram: [@wilbtc](https://t.me/wilbtc)
- GitHub Issues: [agent-as-service/issues](https://github.com/wilbtc/agent-as-service/issues)
