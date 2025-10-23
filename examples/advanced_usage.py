"""
Advanced usage example for Agent as a Service
"""

import asyncio
from aaas import AgentClient

async def main():
    """Advanced usage with multiple agents"""

    # Initialize client with context manager
    with AgentClient(api_key="your-api-key") as client:

        # Deploy multiple agents
        agents = []
        templates = ["customer-service-pro", "data-analysis", "content-creation"]

        for template in templates:
            agent = client.deploy_agent(
                template=template,
                config={
                    "language": "multi",
                    "max_tokens": 8192,
                    "temperature": 0.7
                }
            )
            agents.append(agent)
            print(f"Deployed {template} agent: {agent.id}")

        # Send messages to agents
        messages = [
            "Analyze customer sentiment from recent reviews",
            "Generate a sales report for Q1 2025",
            "Write a blog post about AI trends"
        ]

        for agent, message in zip(agents, messages):
            response = agent.send(message)
            print(f"\nAgent {agent.id} response:")
            print(response[:200] + "..." if len(response) > 200 else response)

        # Monitor agent status
        for agent in agents:
            info = agent.info()
            print(f"\nAgent {agent.id}:")
            print(f"  Status: {info.status}")
            print(f"  Template: {info.config.template}")
            print(f"  Messages: {info.messages_count}")
            print(f"  PID: {info.pid}")

        # Cleanup
        for agent in agents:
            agent.delete()
            print(f"Deleted agent {agent.id}")

if __name__ == "__main__":
    asyncio.run(main())
