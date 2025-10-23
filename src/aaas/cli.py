"""
Command-line interface for AaaS
"""

import sys
import argparse
import json
from typing import Optional

from .server import run_server
from .client import AgentClient
from .config import settings


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Agent as a Service (AaaS) - Enterprise AI Agent Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("serve", help="Start the AaaS server")
    server_parser.add_argument("--host", default=settings.host, help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    server_parser.add_argument("--log-level", default=settings.log_level, help="Log level")

    # Client commands
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a new agent")
    deploy_parser.add_argument("template", help="Agent template")
    deploy_parser.add_argument("--config", help="Configuration JSON string")
    deploy_parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    deploy_parser.add_argument("--api-key", help="API key")

    list_parser = subparsers.add_parser("list", help="List all agents")
    list_parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    list_parser.add_argument("--api-key", help="API key")

    send_parser = subparsers.add_parser("send", help="Send a message to an agent")
    send_parser.add_argument("agent_id", help="Agent ID")
    send_parser.add_argument("message", help="Message to send")
    send_parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    send_parser.add_argument("--api-key", help="API key")

    delete_parser = subparsers.add_parser("delete", help="Delete an agent")
    delete_parser.add_argument("agent_id", help="Agent ID")
    delete_parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    delete_parser.add_argument("--api-key", help="API key")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    if args.command == "serve":
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
        )
        return 0

    elif args.command == "deploy":
        config = json.loads(args.config) if args.config else {}
        with AgentClient(api_key=args.api_key, base_url=args.api_url) as client:
            agent = client.deploy_agent(args.template, config)
            print(f"Agent deployed: {agent.id}")
            print(f"Endpoint: {agent.endpoint}")
            print(f"Status: {agent.status}")
        return 0

    elif args.command == "list":
        with AgentClient(api_key=args.api_key, base_url=args.api_url) as client:
            agents = client.list_agents()
            if not agents:
                print("No agents found")
            else:
                for agent_id, info in agents.items():
                    print(f"Agent ID: {agent_id}")
                    print(f"  Status: {info.status}")
                    print(f"  Template: {info.config.template}")
                    print(f"  Messages: {info.messages_count}")
                    print()
        return 0

    elif args.command == "send":
        with AgentClient(api_key=args.api_key, base_url=args.api_url) as client:
            response = client.send_message(args.agent_id, args.message)
            print(f"Response from agent {response.agent_id}:")
            print(response.response)
        return 0

    elif args.command == "delete":
        with AgentClient(api_key=args.api_key, base_url=args.api_url) as client:
            client.delete_agent(args.agent_id)
            print(f"Agent {args.agent_id} deleted")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
