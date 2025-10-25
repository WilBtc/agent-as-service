"""
FastAPI REST API for Agent as a Service
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .agent_manager import get_agent_manager, AgentManager
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Agent as a Service")
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
    version="1.0.0",
    lifespan=lifespan,
)

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
async def create_agent(
    request: CreateAgentRequest,
    manager: AgentManager = Depends(get_agent_manager),
):
    """Create a new agent instance"""
    try:
        agent_id = await manager.create_agent(request.config, request.auto_start)
        agent = await manager.get_agent(agent_id)

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
async def list_agents(manager: AgentManager = Depends(get_agent_manager)):
    """List all agent instances"""
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
async def get_agent(agent_id: str, manager: AgentManager = Depends(get_agent_manager)):
    """Get information about a specific agent"""
    agent = await manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return agent.get_info()


@app.post(f"{settings.api_prefix}/agents/{{agent_id}}/messages", response_model=AgentResponse)
async def send_message(
    agent_id: str,
    request: MessageRequest,
    manager: AgentManager = Depends(get_agent_manager),
):
    """Send a message to an agent"""
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
        response = await agent.send_message(request.message, request.context)
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
async def start_agent(agent_id: str, manager: AgentManager = Depends(get_agent_manager)):
    """Start an agent"""
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
async def stop_agent(agent_id: str, manager: AgentManager = Depends(get_agent_manager)):
    """Stop an agent"""
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
async def delete_agent(agent_id: str, manager: AgentManager = Depends(get_agent_manager)):
    """Delete an agent"""
    success = await manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    return {"status": "success", "message": f"Agent {agent_id} deleted"}


@app.get(f"{settings.api_prefix}/agent-types")
async def list_agent_types():
    """List all available agent types and their configurations"""
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
async def quick_query(
    request: MessageRequest,
    agent_type: AgentType = AgentType.GENERAL,
    manager: AgentManager = Depends(get_agent_manager),
):
    """
    Quick query endpoint - creates a temporary agent, sends message, and returns response.
    This is useful for one-off queries without needing to manage agent lifecycle.
    """
    try:
        response = await manager.query_agent(request.message, agent_type)
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
