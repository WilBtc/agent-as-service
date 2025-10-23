# Technical Documentation

## Overview

Agent as a Service (AaaS) is a Python-based platform that manages Claude Code instances as subprocesses, providing a REST API and client library for easy integration.

## Architecture

### System Components

1. **Agent Manager** (`agent_manager.py`)
   - Manages multiple Claude Code subprocess instances
   - Handles process lifecycle (start, stop, restart)
   - Routes messages between API and agents
   - Implements process pooling and resource management

2. **API Server** (`api.py`)
   - FastAPI-based REST API
   - Handles HTTP requests
   - Manages authentication and authorization
   - Provides endpoints for CRUD operations

3. **Client Library** (`client.py`)
   - Python SDK for programmatic access
   - Abstracts API communication
   - Provides high-level interface for agent management

4. **CLI Tool** (`cli.py`)
   - Command-line interface
   - Quick operations without coding
   - Server management

### Component Interaction

```
User Application
       │
       ├─── Python Client (client.py)
       ├─── HTTP API Calls
       └─── CLI Commands (cli.py)
              │
              ▼
       FastAPI Server (api.py)
              │
              ▼
       Agent Manager (agent_manager.py)
              │
              ├─── Agent 1 (ClaudeCodeAgent)
              │         └─── Claude Code Process
              │
              ├─── Agent 2 (ClaudeCodeAgent)
              │         └─── Claude Code Process
              │
              └─── Agent N (ClaudeCodeAgent)
                        └─── Claude Code Process
```

## Claude Code Integration

### Subprocess Management

Each agent runs as an isolated subprocess:

```python
self.process = await asyncio.create_subprocess_exec(
    *cmd,
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    env=env,
    cwd=self.working_dir,
)
```

Key aspects:
- **Isolation**: Each agent runs in its own process
- **Environment**: Custom environment variables per agent
- **Working Directory**: Separate workspace for each agent
- **I/O Streams**: Bidirectional communication via stdin/stdout

### Communication Protocol

Communication with Claude Code subprocesses uses stdin/stdout:

```
Client → API → Agent Manager → Claude Code Process
                                      │
Client ← API ← Agent Manager ← stdout ┘
```

**Sending Messages:**
1. Client sends message to API
2. API routes to Agent Manager
3. Manager writes to subprocess stdin
4. Response read from stdout

**Reading Responses:**
- Continuous reader task monitors stdout
- Buffers output until response complete
- Returns aggregated response to client

### Process Lifecycle

#### Starting an Agent

```python
async def start(self) -> bool:
    # Create working directory
    Path(self.working_dir).mkdir(parents=True, exist_ok=True)

    # Prepare environment
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = settings.claude_api_key

    # Start subprocess
    self.process = await asyncio.create_subprocess_exec(...)

    # Start output reader
    self._reader_task = asyncio.create_task(self._read_output())

    self.status = AgentStatus.RUNNING
```

#### Stopping an Agent

```python
async def stop(self) -> bool:
    # Cancel reader task
    self._reader_task.cancel()

    # Graceful termination
    self.process.terminate()
    await asyncio.wait_for(self.process.wait(), timeout=5.0)

    # Force kill if necessary
    if timeout:
        self.process.kill()
        await self.process.wait()
```

## Data Models

### AgentConfig

Configuration for an agent instance:

```python
class AgentConfig(BaseModel):
    template: str
    language: Optional[str] = "en"
    personality: Optional[str] = "professional"
    integration: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 1.0
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = {}
```

### AgentStatus

Agent lifecycle states:

- `STARTING`: Agent initialization in progress
- `RUNNING`: Agent active and ready
- `STOPPED`: Agent intentionally stopped
- `ERROR`: Agent encountered an error
- `TERMINATED`: Process has ended

### AgentInfo

Runtime information about an agent:

```python
class AgentInfo(BaseModel):
    id: str
    status: AgentStatus
    config: AgentConfig
    created_at: datetime
    endpoint: str
    pid: Optional[int]
    messages_count: int
```

## API Endpoints

### Agent Management

- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{id}` - Get agent info
- `DELETE /api/v1/agents/{id}` - Delete agent

### Agent Operations

- `POST /api/v1/agents/{id}/start` - Start agent
- `POST /api/v1/agents/{id}/stop` - Stop agent
- `POST /api/v1/agents/{id}/messages` - Send message

### System

- `GET /` - Service info
- `GET /health` - Health check

## Concurrency & Threading

### Async/Await Pattern

AaaS uses Python's asyncio for concurrent operations:

- **Non-blocking I/O**: All subprocess I/O is async
- **Task Management**: Multiple agents run concurrently
- **Lock Management**: Prevents race conditions

```python
# Example: Concurrent agent creation
async def create_multiple_agents(configs):
    tasks = [manager.create_agent(cfg) for cfg in configs]
    agent_ids = await asyncio.gather(*tasks)
    return agent_ids
```

### Resource Management

```python
class AgentManager:
    def __init__(self):
        self.agents: Dict[str, ClaudeCodeAgent] = {}
        self._lock = asyncio.Lock()

    async def create_agent(self, config):
        async with self._lock:
            # Thread-safe agent creation
            agent_id = str(uuid.uuid4())
            self.agents[agent_id] = ClaudeCodeAgent(...)
```

## Configuration

### Environment Variables

Loaded via `pydantic-settings`:

```python
class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    claude_code_path: str = "claude"
    claude_api_key: Optional[str] = None
    max_agents: int = 100

    class Config:
        env_file = ".env"
```

### Configuration Hierarchy

1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

## Error Handling

### API Level

FastAPI handles validation and HTTP errors:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### Agent Level

Process errors are caught and reported:

```python
try:
    await agent.send_message(message)
except asyncio.TimeoutError:
    raise HTTPException(status_code=504, detail="Agent timeout")
except Exception as e:
    logger.error(f"Agent error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## Performance Considerations

### Subprocess Overhead

- Each agent requires a separate process
- Memory: ~100-500MB per Claude Code instance
- CPU: Depends on workload
- Recommendation: Monitor and scale based on load

### Scaling Strategies

1. **Vertical Scaling**
   - Increase MAX_AGENTS
   - Add more CPU/RAM to host

2. **Horizontal Scaling**
   - Run multiple AaaS instances
   - Use load balancer
   - Shared state via Redis/database

3. **Process Pooling**
   - Reuse agent processes
   - Implement connection pooling

## Security

### API Security

- API key authentication (X-API-Key header)
- CORS configuration
- Input validation via Pydantic

### Process Security

- Isolated working directories
- Environment variable isolation
- Process resource limits

### Recommendations

1. Use HTTPS in production
2. Implement rate limiting
3. Validate all inputs
4. Limit subprocess permissions
5. Monitor for abuse

## Logging

### Log Levels

- `DEBUG`: Detailed subprocess communication
- `INFO`: Agent lifecycle events
- `WARNING`: Non-critical issues
- `ERROR`: Failures and exceptions

### Log Format

Configurable via LOG_FORMAT:
- `json`: Structured JSON logs
- `text`: Human-readable text

### Example

```python
logger.info(f"Agent {agent_id} started with PID {pid}")
logger.error(f"Failed to start agent: {error}")
```

## Testing

### Unit Tests

Test individual components:

```python
@pytest.mark.asyncio
async def test_create_agent(agent_manager):
    agent_id = await agent_manager.create_agent(config)
    assert agent_id is not None
```

### Integration Tests

Test API endpoints:

```python
def test_create_agent_endpoint(client):
    response = client.post("/api/v1/agents", json=payload)
    assert response.status_code == 201
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=aaas

# Specific test
pytest tests/test_api.py::test_create_agent
```

## Deployment

### Production Checklist

- [ ] Set ANTHROPIC_API_KEY
- [ ] Configure LOG_LEVEL=WARNING
- [ ] Set MAX_AGENTS appropriately
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Implement rate limiting
- [ ] Review security settings

### Docker

Recommended for production:

```bash
docker-compose up -d
```

Benefits:
- Consistent environment
- Easy scaling
- Resource isolation
- Simple updates

## Troubleshooting

### Common Issues

**Agent won't start**
- Check ANTHROPIC_API_KEY is set
- Verify Claude Code is installed
- Check working directory permissions

**Timeout errors**
- Increase AGENT_TIMEOUT
- Check Claude Code responsiveness
- Review system resources

**Memory issues**
- Reduce MAX_AGENTS
- Implement agent recycling
- Monitor with `docker stats` or `top`

## Future Enhancements

### Planned Features

1. **Persistent Storage**
   - Save agent state to database
   - Resume agents after restart

2. **Advanced Routing**
   - Load balancing across agents
   - Intelligent agent selection

3. **Monitoring Dashboard**
   - Real-time metrics
   - Agent performance tracking

4. **WebSocket Support**
   - Real-time communication
   - Streaming responses

5. **Agent Templates**
   - Pre-configured agent types
   - Custom template marketplace

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Support

- Documentation: [docs/](.)
- Telegram: [@wilbtc](https://t.me/wilbtc)
- Issues: GitHub Issues
