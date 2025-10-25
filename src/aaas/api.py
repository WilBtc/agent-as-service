"""
FastAPI REST API for Agent as a Service
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .agent_manager import get_agent_manager, AgentManager
from .auth import verify_api_key, verify_api_key_optional
from .config import get_settings, init_directories, settings
from .models import (
    AgentInfo,
    AgentResponse,
    CreateAgentRequest,
    CreateAgentResponse,
    MessageRequest,
    AgentStatus,
    AgentType,
    AGENT_TYPE_CONFIGS,
)
from .metrics import (
    get_metrics,
    track_http_request,
    track_rate_limit_exceeded,
    update_system_metrics,
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Configure rate limiter
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Agent as a Service v2.0.0")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Rate limiting: {'enabled' if settings.rate_limit_enabled else 'disabled'}")
    logger.info(f"API authentication: {'enabled' if settings.require_api_key else 'disabled'}")
    logger.info(f"Auto-scaling: {'enabled' if settings.enable_autoscaling else 'disabled'}")
    logger.info(f"Health monitoring: {'enabled' if settings.enable_health_monitoring else 'disabled'}")
    logger.info(f"Metrics: {'enabled' if settings.metrics_enabled else 'disabled'}")

    init_directories()

    # Start autoscaler
    manager = get_agent_manager()
    if manager.autoscaler:
        await manager.autoscaler.start()
        logger.info("Autoscaler started")

    # Start system metrics updates
    import asyncio
    async def update_metrics_loop():
        while True:
            try:
                update_system_metrics()
                await asyncio.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logger.error(f"Error updating system metrics: {e}")

    metrics_task = None
    if settings.metrics_enabled:
        metrics_task = asyncio.create_task(update_metrics_loop())
        logger.info("System metrics monitoring started")

    yield

    # Shutdown
    logger.info("Shutting down Agent as a Service")

    # Stop metrics task
    if metrics_task:
        metrics_task.cancel()
        try:
            await metrics_task
        except asyncio.CancelledError:
            pass

    # Shutdown manager (includes autoscaler)
    await manager.shutdown_all()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Agent as a Service (AaaS)",
    description="Enterprise AI Agent Platform - Deploy and manage Claude Code agents at scale",
    version="2.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add metrics tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track HTTP requests with metrics"""
    start_time = time.time()

    # Track rate limit exceeded
    try:
        response = await call_next(request)
    except RateLimitExceeded:
        track_rate_limit_exceeded(str(request.url.path))
        raise

    # Track request metrics
    duration = time.time() - start_time
    track_http_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=duration
    )

    return response


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agent as a Service",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    manager = get_agent_manager()
    agents = await manager.list_agents()

    # Count agents by status
    status_counts = {}
    for agent_info in agents.values():
        status = agent_info.status.value if hasattr(agent_info.status, 'value') else str(agent_info.status)
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "status": "healthy",
        "agents_count": len(agents),
        "max_agents": settings.max_agents,
        "min_agents": settings.min_agents,
        "agents_by_status": status_counts,
        "autoscaling_enabled": settings.enable_autoscaling,
        "health_monitoring_enabled": settings.enable_health_monitoring,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics not enabled")

    return get_metrics()


@app.get("/autoscaler/stats")
async def autoscaler_stats():
    """Get autoscaler statistics"""
    manager = get_agent_manager()

    if not manager.autoscaler:
        return {
            "enabled": False,
            "message": "Autoscaling is not enabled"
        }

    stats = manager.autoscaler.get_stats()
    agents = await manager.list_agents()

    # Add current agent counts by status
    status_counts = {}
    for agent_info in agents.values():
        status = agent_info.status.value if hasattr(agent_info.status, 'value') else str(agent_info.status)
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        **stats,
        "current_agents": len(agents),
        "agents_by_status": status_counts,
    }


@app.post(
    f"{settings.api_prefix}/agents",
    response_model=CreateAgentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(f"{settings.rate_limit_agent_creation}/minute")
async def create_agent(
    request: Request,
    create_request: CreateAgentRequest,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """Create a new agent instance (Protected: requires API key, rate limited)"""
    try:
        agent_id = await manager.create_agent(create_request.config, create_request.auto_start)
        agent = await manager.get_agent(agent_id)

        logger.info(f"Agent created: {agent_id} (authenticated: {api_key != 'disabled'})")

        return CreateAgentResponse(
            agent_id=agent_id,
            status=agent.status if agent else AgentStatus.ERROR,
            endpoint=f"{settings.api_prefix}/agents/{agent_id}",
            message=f"Agent created successfully with ID: {agent_id}",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent",
        )


@app.get(f"{settings.api_prefix}/agents", response_model=Dict[str, AgentInfo])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_agents(
    request: Request,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """List all agent instances (Protected: requires API key, rate limited)"""
    try:
        agents = await manager.list_agents()
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list agents",
        )


@app.get(f"{settings.api_prefix}/agents/{{agent_id}}", response_model=AgentInfo)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_agent(
    request: Request,
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """Get information about a specific agent (Protected: requires API key, rate limited)"""
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return agent.get_info()


@app.post(f"{settings.api_prefix}/agents/{{agent_id}}/messages", response_model=AgentResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def send_message(
    request: Request,
    agent_id: str,
    message_request: MessageRequest,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """Send a message to an agent (Protected: requires API key, rate limited)"""
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    if agent.status != AgentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent {agent_id} is not running (status: {agent.status})",
        )

    try:
        response = await agent.send_message(message_request.message, message_request.context)
        return AgentResponse(
            agent_id=agent_id,
            response=response,
            timestamp=agent.created_at,
            metadata={"messages_count": agent.messages_count},
        )
    except Exception as e:
        logger.error(f"Error sending message to agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@app.post(f"{settings.api_prefix}/agents/{{agent_id}}/start")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def start_agent(
    request: Request,
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """Start an agent (Protected: requires API key, rate limited)"""
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    try:
        success = await agent.start()
        if success:
            return {"status": "success", "message": f"Agent {agent_id} started"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start agent",
            )
    except Exception as e:
        logger.error(f"Error starting agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post(f"{settings.api_prefix}/agents/{{agent_id}}/stop")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def stop_agent(
    request: Request,
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """Stop an agent (Protected: requires API key, rate limited)"""
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    try:
        success = await agent.stop()
        if success:
            return {"status": "success", "message": f"Agent {agent_id} stopped"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop agent",
            )
    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.delete(f"{settings.api_prefix}/agents/{{agent_id}}")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def delete_agent(
    request: Request,
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """Delete an agent (Protected: requires API key, rate limited)"""
    success = await manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return {"status": "success", "message": f"Agent {agent_id} deleted"}


@app.get(f"{settings.api_prefix}/agent-types")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_agent_types(
    request: Request,
    api_key: str = Depends(verify_api_key_optional),
):
    """List all available agent types and their configurations (Optional auth, rate limited)"""
    agent_types_info = {}
    for agent_type in AgentType:
        config = AGENT_TYPE_CONFIGS.get(agent_type, {})
        agent_types_info[agent_type.value] = {
            "type": agent_type.value,
            "description": config.get("description", ""),
            "allowed_tools": config.get("allowed_tools", []),
            "permission_mode": config.get("permission_mode", "ask"),
        }
    return agent_types_info


@app.post(f"{settings.api_prefix}/query", response_model=AgentResponse)
@limiter.limit("20/minute")  # Lower limit for resource-intensive queries
async def quick_query(
    request: Request,
    message_request: MessageRequest,
    agent_type: AgentType = AgentType.GENERAL,
    manager: AgentManager = Depends(get_agent_manager),
    api_key: str = Depends(verify_api_key),
):
    """
    Quick query endpoint - creates a temporary agent, sends message, and returns response.
    This is useful for one-off queries without needing to manage agent lifecycle.
    (Protected: requires API key, rate limited to 20/min)
    """
    try:
        response = await manager.query_agent(message_request.message, agent_type)
        return AgentResponse(
            agent_id="quick-query",
            response=response,
            timestamp=datetime.now(timezone.utc),
            metadata={"agent_type": agent_type.value, "query_type": "quick"},
        )
    except Exception as e:
        logger.error(f"Error in quick query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}",
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
