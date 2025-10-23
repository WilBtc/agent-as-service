"""
Server startup script for AaaS
"""

import logging
import sys

import uvicorn

from .config import settings


def run_server(
    host: str = None,
    port: int = None,
    reload: bool = False,
    log_level: str = None,
):
    """
    Run the AaaS server

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
        log_level: Logging level
    """
    config = {
        "app": "aaas.api:app",
        "host": host or settings.host,
        "port": port or settings.port,
        "reload": reload,
        "log_level": (log_level or settings.log_level).lower(),
    }

    logging.info(f"Starting AaaS server on {config['host']}:{config['port']}")
    uvicorn.run(**config)


if __name__ == "__main__":
    run_server()
