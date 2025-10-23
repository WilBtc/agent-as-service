"""
Example: Running the AaaS API server
"""

from aaas.server import run_server

if __name__ == "__main__":
    # Start the server with custom configuration
    run_server(
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="INFO"
    )
