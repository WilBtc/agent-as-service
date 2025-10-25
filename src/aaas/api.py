"""
FastAPI REST API for Agent as a Service
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
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
    logger.info("Starting Agent as a Service")
    logger.info(f"Rate limiting: {'enabled' if settings.rate_limit_enabled else 'disabled'}")
    logger.info(f"API authentication: {'enabled' if settings.require_api_key else 'disabled'}")
    init_directories()
    yield
    # Shutdown
    logger.info("Shutting down Agent as a Service")
    manager = get_agent_manager()
    await manager.shutdown_all()


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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agent as a Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    manager = get_agent_manager()
    agents = await manager.list_agents()
    return {
        "status": "healthy",
        "agents_count": len(agents),
        "max_agents": settings.max_agents,
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

        logger.info(f"Agent created: {agent_id} (API key: {api_key[:8] if api_key != 'disabled' else 'disabled'}...)")

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
            timestamp=datetime.utcnow(),
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
