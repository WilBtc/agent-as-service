"""
Advanced usage example for Agent as a Service
Demonstrates multiple specialized agents working together using Claude Agent SDK
"""

import asyncio
from aaas import AgentClient, AgentType, PermissionMode

async def main():
    """Advanced usage with multiple specialized agents"""

    print("=== Agent as a Service - Advanced Multi-Agent Usage ===\n")

    # Initialize client with context manager
    with AgentClient(api_key="your-api-key", timeout=120.0) as client:

        # Deploy multiple specialized agents with different types
        print("Deploying specialized agents...\n")

        # Research Agent - for comprehensive analysis
        research_agent = client.deploy_agent(
            agent_type=AgentType.RESEARCH,
            config={
                "language": "en",
                "max_tokens": 8192,
                "temperature": 0.7,
                "permission_mode": PermissionMode.ACCEPT_EDITS,
                "system_prompt": "You are a research specialist focused on AI technology trends."
            }
        )
        print(f"✓ Research Agent deployed: {research_agent.id}")

        # Code Agent - for development tasks
        code_agent = client.deploy_agent(
            agent_type=AgentType.CODE,
            config={
                "language": "en",
                "max_tokens": 8192,
                "temperature": 0.5,
                "permission_mode": PermissionMode.ACCEPT_EDITS,
                "allowed_tools": ["Read", "Write", "Edit", "Bash", "Grep"]
            }
        )
        print(f"✓ Code Agent deployed: {code_agent.id}")

        # Finance Agent - for financial analysis
        finance_agent = client.deploy_agent(
            agent_type=AgentType.FINANCE,
            config={
                "language": "en",
                "max_tokens": 4096,
                "temperature": 0.3,
                "permission_mode": PermissionMode.ASK
            }
        )
        print(f"✓ Finance Agent deployed: {finance_agent.id}")

        # Data Analysis Agent - for data insights
        data_agent = client.deploy_agent(
            agent_type=AgentType.DATA_ANALYSIS,
            config={
                "language": "en",
                "max_tokens": 8192,
                "temperature": 0.6,
                "permission_mode": PermissionMode.ACCEPT_EDITS
            }
        )
        print(f"✓ Data Analysis Agent deployed: {data_agent.id}\n")

        # Create a list of agents with their tasks
        agent_tasks = [
            (research_agent, "Research the latest developments in Claude Agent SDK and summarize key features"),
            (code_agent, "Review best practices for implementing error handling in Python async code"),
            (finance_agent, "Explain the key metrics to evaluate when analyzing a tech startup's finances"),
            (data_agent, "Describe the most effective techniques for analyzing large datasets in Python")
        ]

        # Send messages to all agents
        print("Sending tasks to agents...\n")
        for agent, message in agent_tasks:
            print(f"Task for Agent {agent.id}:")
            print(f"  Message: {message[:80]}...")

            response = agent.send(message)
            print(f"  Response: {response[:150]}...")
            print()

        # Monitor agent status
        print("\n=== Agent Status Report ===\n")
        all_agents = [research_agent, code_agent, finance_agent, data_agent]
        agent_names = ["Research", "Code", "Finance", "Data Analysis"]

        for agent, name in zip(all_agents, agent_names):
            info = agent.info()
            print(f"{name} Agent ({agent.id}):")
            print(f"  Status: {info.status}")
            print(f"  Agent Type: {info.config.agent_type}")
            print(f"  Messages: {info.messages_count}")
            print(f"  Model: {info.config.model}")
            print(f"  Permission Mode: {info.config.permission_mode}")
            print()

        # Demonstrate quick queries for comparison
        print("=== Quick Query Demo ===\n")
        print("Comparing responses from different agent types...\n")

        question = "What are the benefits of using AI agents?"

        for agent_type in [AgentType.GENERAL, AgentType.RESEARCH, AgentType.CODE]:
            print(f"{agent_type.value.upper()} Agent quick query:")
            response = client.quick_query(question, agent_type=agent_type)
            print(f"  {response[:100]}...\n")

        # List all active agents
        all_active = client.list_agents()
        print(f"Total active agents: {len(all_active)}\n")

        # Cleanup
        print("Cleaning up agents...")
        for agent in all_agents:
            agent.stop()
            agent.delete()
            print(f"✓ Deleted agent {agent.id}")

        print("\nAll agents cleaned up successfully!")

if __name__ == "__main__":
    asyncio.run(main())
