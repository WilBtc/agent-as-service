"""
MCP Server Manager - Adaptive provisioning and lifecycle management

Handles dynamic provisioning of MCP servers based on agent requirements,
resource pooling, health monitoring, and automatic cleanup.
"""

import asyncio
import logging
import uuid
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from collections import defaultdict

from .mcp_models import (
    MCPServerType,
    MCPServerStatus,
    MCPServerConfig,
    MCPServerInfo,
    get_mcp_servers_for_agent_type,
    get_mcp_server_config,
    validate_mcp_server_env,
    MCP_SERVER_CATALOG,
)
from .config import settings

logger = logging.getLogger(__name__)


class MCPServer:
    """Manages a single MCP server instance"""

    def __init__(self, server_id: str, config: MCPServerConfig, env: Dict[str, str]):
        self.server_id = server_id
        self.config = config
        self.env = env
        self.status = MCPServerStatus.STOPPED
        self.created_at = datetime.now(timezone.utc)
        self.last_health_check: Optional[datetime] = None
        self.connected_agents: Set[str] = set()
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.endpoint: Optional[str] = None
        self.error_message: Optional[str] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._idle_check_task: Optional[asyncio.Task] = None

    async def start(self) -> bool:
        """Start the MCP server"""
        if self.status == MCPServerStatus.RUNNING:
            logger.warning(f"MCP server {self.server_id} already running")
            return True

        try:
            logger.info(f"Starting MCP server {self.server_id} ({self.config.server_type})")
            self.status = MCPServerStatus.STARTING

            # Merge environment variables
            full_env = {**self.env, **self.config.env}

            # Check required environment variables
            if not validate_mcp_server_env(self.config.server_type, full_env):
                if not self.config.optional:
                    self.error_message = f"Missing required environment variables for {self.config.server_type}"
                    logger.error(self.error_message)
                    self.status = MCPServerStatus.ERROR
                    return False
                else:
                    logger.warning(f"Skipping optional MCP server {self.config.server_type}: missing env vars")
                    self.status = MCPServerStatus.STOPPED
                    return True  # Don't fail for optional servers

            # Start the server process
            # Note: In production, this would use proper subprocess management
            # For now, we're simulating the server start
            self.status = MCPServerStatus.RUNNING
            self.pid = None  # Would be process.pid in real implementation
            self.endpoint = f"stdio://{self.config.server_type}"

            # Start health monitoring
            if settings.enable_health_monitoring:
                self._health_check_task = asyncio.create_task(self._health_check_loop())

            # Start idle monitoring
            self._idle_check_task = asyncio.create_task(self._idle_check_loop())

            logger.info(f"MCP server {self.server_id} started successfully")
            return True

        except Exception as e:
            self.status = MCPServerStatus.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to start MCP server {self.server_id}: {e}", exc_info=True)
            return False

    async def stop(self) -> bool:
        """Stop the MCP server"""
        try:
            logger.info(f"Stopping MCP server {self.server_id}")
            self.status = MCPServerStatus.STOPPING

            # Cancel monitoring tasks
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            if self._idle_check_task:
                self._idle_check_task.cancel()
                try:
                    await self._idle_check_task
                except asyncio.CancelledError:
                    pass

            # Stop the process (simulated for now)
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)

            self.status = MCPServerStatus.STOPPED
            self.pid = None
            logger.info(f"MCP server {self.server_id} stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop MCP server {self.server_id}: {e}")
            return False

    async def _health_check_loop(self):
        """Periodic health check"""
        while self.status == MCPServerStatus.RUNNING:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # Simple health check - verify process is still running
                is_healthy = await self._check_health()
                self.last_health_check = datetime.now(timezone.utc)

                if not is_healthy:
                    logger.warning(f"MCP server {self.server_id} failed health check")
                    self.status = MCPServerStatus.ERROR
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in MCP server health check loop: {e}")

    async def _check_health(self) -> bool:
        """Check if server is healthy"""
        # Simplified health check - would ping the actual server in production
        return self.status == MCPServerStatus.RUNNING

    async def _idle_check_loop(self):
        """Monitor for idle timeout"""
        while self.status == MCPServerStatus.RUNNING:
            try:
                await asyncio.sleep(60)  # Check every minute

                if len(self.connected_agents) == 0:
                    # Server is idle - check timeout
                    idle_time = (datetime.now(timezone.utc) - self.created_at).total_seconds()

                    # If no agents ever connected, use creation time
                    # If agents connected before, use last health check time
                    if self.last_health_check:
                        idle_time = (datetime.now(timezone.utc) - self.last_health_check).total_seconds()

                    if idle_time > self.config.idle_timeout and len(self.connected_agents) == 0:
                        logger.info(f"MCP server {self.server_id} idle timeout, shutting down")
                        await self.stop()
                        break

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in MCP server idle check loop: {e}")

    def connect_agent(self, agent_id: str) -> bool:
        """Register an agent connection"""
        if len(self.connected_agents) >= self.config.max_connections:
            logger.warning(f"MCP server {self.server_id} at max connections")
            return False

        self.connected_agents.add(agent_id)
        logger.debug(f"Agent {agent_id} connected to MCP server {self.server_id}")
        return True

    def disconnect_agent(self, agent_id: str):
        """Unregister an agent connection"""
        self.connected_agents.discard(agent_id)
        logger.debug(f"Agent {agent_id} disconnected from MCP server {self.server_id}")

    def get_info(self) -> MCPServerInfo:
        """Get server information"""
        return MCPServerInfo(
            server_id=self.server_id,
            server_type=self.config.server_type,
            status=self.status,
            created_at=self.created_at,
            last_health_check=self.last_health_check,
            connected_agents=list(self.connected_agents),
            connection_count=len(self.connected_agents),
            pid=self.pid,
            endpoint=self.endpoint,
            error_message=self.error_message,
        )


class MCPServerManager:
    """Manages all MCP servers with adaptive provisioning"""

    def __init__(self, global_env: Optional[Dict[str, str]] = None):
        self.servers: Dict[str, MCPServer] = {}
        self.global_env = global_env or {}
        self._lock = asyncio.Lock()

        # Track which servers are used by which agent types
        self.agent_server_mapping: Dict[str, List[str]] = defaultdict(list)

        # Server type to server ID mapping for sharing
        self.server_type_to_id: Dict[MCPServerType, List[str]] = defaultdict(list)

    async def provision_for_agent(self, agent_id: str, agent_type: str) -> List[str]:
        """
        Adaptively provision MCP servers for an agent based on its type.

        Args:
            agent_id: The agent identifier
            agent_type: The agent type (e.g., 'research', 'code')

        Returns:
            List of server IDs provisioned for this agent
        """
        required_servers = get_mcp_servers_for_agent_type(agent_type)
        provisioned_servers = []

        logger.info(f"Provisioning MCP servers for agent {agent_id} ({agent_type}): {required_servers}")

        for server_type in required_servers:
            server_id = await self._get_or_create_server(server_type)
            if server_id:
                # Connect the agent to the server
                server = self.servers.get(server_id)
                if server and server.connect_agent(agent_id):
                    provisioned_servers.append(server_id)
                    self.agent_server_mapping[agent_id].append(server_id)

        logger.info(f"Provisioned {len(provisioned_servers)} MCP servers for agent {agent_id}")
        return provisioned_servers

    async def _get_or_create_server(self, server_type: MCPServerType) -> Optional[str]:
        """
        Get an existing shared server or create a new one.

        Args:
            server_type: The type of MCP server

        Returns:
            Server ID or None if failed
        """
        config = get_mcp_server_config(server_type)
        if not config:
            logger.error(f"No configuration found for MCP server type {server_type}")
            return None

        async with self._lock:
            # If server is shareable, try to find an existing one
            if config.shared:
                existing_servers = self.server_type_to_id.get(server_type, [])
                for server_id in existing_servers:
                    server = self.servers.get(server_id)
                    if server and server.status == MCPServerStatus.RUNNING:
                        if len(server.connected_agents) < config.max_connections:
                            logger.info(f"Reusing existing MCP server {server_id} ({server_type})")
                            return server_id

            # Create new server
            server_id = str(uuid.uuid4())
            server = MCPServer(server_id, config, self.global_env)

            # Start the server
            success = await server.start()
            if success:
                self.servers[server_id] = server
                self.server_type_to_id[server_type].append(server_id)
                logger.info(f"Created new MCP server {server_id} ({server_type})")
                return server_id
            elif not config.optional:
                logger.error(f"Failed to start required MCP server {server_type}")
                return None
            else:
                logger.warning(f"Failed to start optional MCP server {server_type}, continuing")
                return None

    async def deprovision_for_agent(self, agent_id: str):
        """
        Remove agent connections from MCP servers.

        Args:
            agent_id: The agent identifier
        """
        server_ids = self.agent_server_mapping.get(agent_id, [])

        for server_id in server_ids:
            server = self.servers.get(server_id)
            if server:
                server.disconnect_agent(agent_id)

                # If server becomes idle and is not shared, stop it
                if len(server.connected_agents) == 0 and not server.config.shared:
                    logger.info(f"Stopping non-shared idle MCP server {server_id}")
                    await server.stop()
                    await self._cleanup_server(server_id)

        # Remove agent from mapping
        if agent_id in self.agent_server_mapping:
            del self.agent_server_mapping[agent_id]

        logger.info(f"Deprovisioned MCP servers for agent {agent_id}")

    async def _cleanup_server(self, server_id: str):
        """Remove a stopped server from tracking"""
        async with self._lock:
            server = self.servers.get(server_id)
            if server:
                # Remove from type mapping
                server_ids = self.server_type_to_id.get(server.config.server_type, [])
                if server_id in server_ids:
                    server_ids.remove(server_id)

                # Remove from servers dict
                del self.servers[server_id]

    async def get_server_info(self, server_id: str) -> Optional[MCPServerInfo]:
        """Get information about a specific server"""
        server = self.servers.get(server_id)
        return server.get_info() if server else None

    async def list_servers(self) -> Dict[str, MCPServerInfo]:
        """List all MCP servers"""
        return {
            server_id: server.get_info()
            for server_id, server in self.servers.items()
        }

    async def get_servers_for_agent(self, agent_id: str) -> List[MCPServerInfo]:
        """Get all MCP servers connected to an agent"""
        server_ids = self.agent_server_mapping.get(agent_id, [])
        return [
            self.servers[sid].get_info()
            for sid in server_ids
            if sid in self.servers
        ]

    async def shutdown_all(self):
        """Shutdown all MCP servers"""
        logger.info("Shutting down all MCP servers")

        tasks = [server.stop() for server in self.servers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

        self.servers.clear()
        self.agent_server_mapping.clear()
        self.server_type_to_id.clear()


# Global MCP server manager instance
_mcp_manager: Optional[MCPServerManager] = None


def get_mcp_manager(env: Optional[Dict[str, str]] = None) -> MCPServerManager:
    """Get or create the global MCP server manager"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPServerManager(env)
    return _mcp_manager
