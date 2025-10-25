"""
Example: Using AaaS Hosted Service

This example demonstrates how to use the hosted AaaS service.
Perfect for customers who don't want to manage infrastructure.

Prerequisites:
1. pip install aaas-client
2. Get API key from @wilbtc on Telegram
"""

from aaas import AgentClient, AgentType, PermissionMode


def main():
    """Main example showcasing hosted service usage"""

    print("=== AaaS Hosted Service Example ===\n")

    # STEP 1: Connect to hosted service
    # Replace with your actual API key and service URL
    client = AgentClient(
        base_url="https://api.aaas.wilbtc.com",  # Hosted service URL
        api_key="your-api-key-here",  # Get from @wilbtc
        timeout=120.0
    )

    print("✓ Connected to AaaS Hosted Service\n")

    # STEP 2: Discover available agent types
    print("Available Agent Types:")
    agent_types = client.list_agent_types()
    for type_name, info in agent_types.items():
        print(f"  • {type_name}: {info['description']}")
    print()

    # STEP 3: Quick query (no agent management needed)
    print("=== Quick Query Example ===")
    print("Asking research agent about AI trends...\n")

    quick_response = client.quick_query(
        "What are the top 3 AI trends in 2025?",
        agent_type=AgentType.RESEARCH
    )
    print(f"Response: {quick_response}\n")

    # STEP 4: Deploy a persistent agent for conversations
    print("=== Persistent Agent Example ===")
    print("Deploying a customer support agent...\n")

    support_agent = client.deploy_agent(
        agent_type=AgentType.CUSTOMER_SUPPORT,
        config={
            "personality": "friendly and professional",
            "language": "en",
            "permission_mode": PermissionMode.ASK
        }
    )

    print(f"✓ Agent deployed: {support_agent.id}\n")

    # Have a conversation
    print("Conversation with support agent:")
    questions = [
        "How can I reset my password?",
        "What if I don't receive the reset email?",
        "Thanks for your help!"
    ]

    for question in questions:
        print(f"User: {question}")
        response = support_agent.send(question)
        print(f"Agent: {response[:200]}...\n")

    # Check agent info
    info = support_agent.info()
    print(f"Agent handled {info.messages_count} messages")
    print(f"Agent status: {info.status}\n")

    # STEP 5: Multi-agent workflow
    print("=== Multi-Agent Workflow Example ===")
    print("Using multiple specialized agents together...\n")

    # Deploy specialized agents
    research_agent = client.deploy_agent(
        agent_type=AgentType.RESEARCH,
        config={"temperature": 0.7, "max_tokens": 4096}
    )

    code_agent = client.deploy_agent(
        agent_type=AgentType.CODE,
        config={"temperature": 0.5, "permission_mode": PermissionMode.ACCEPT_EDITS}
    )

    print("✓ Deployed Research and Code agents\n")

    # Workflow: Research → Code → Analyze
    print("1. Research agent: Finding best practices...")
    research_result = research_agent.send(
        "What are the best practices for building REST APIs in Python?"
    )
    print(f"   Found: {research_result[:100]}...\n")

    print("2. Code agent: Implementing based on research...")
    code_result = code_agent.send(
        f"Create a simple REST API example following: {research_result[:200]}"
    )
    print(f"   Created: {code_result[:100]}...\n")

    # STEP 6: Monitor all agents
    print("=== Agent Monitoring ===")
    all_agents = client.list_agents()
    print(f"Total active agents: {len(all_agents)}\n")

    for agent_id, agent_info in all_agents.items():
        print(f"Agent {agent_id[:8]}...")
        print(f"  Type: {agent_info.config.agent_type}")
        print(f"  Status: {agent_info.status}")
        print(f"  Messages: {agent_info.messages_count}")

    print()

    # STEP 7: Cleanup
    print("=== Cleanup ===")
    print("Deleting all agents...")

    support_agent.delete()
    print("✓ Deleted support agent")

    research_agent.delete()
    print("✓ Deleted research agent")

    code_agent.delete()
    print("✓ Deleted code agent")

    # Check health
    health = client.health_check()
    print(f"\nService Health: {health['status']}")
    print(f"Active agents: {health['agents_count']}/{health['max_agents']}")

    client.close()
    print("\n✓ Session complete!")


def simple_chatbot_example():
    """Simple interactive chatbot example"""

    print("\n=== Interactive Chatbot Example ===")
    print("This creates a simple chatbot using the hosted service.\n")

    client = AgentClient(
        base_url="https://api.aaas.wilbtc.com",
        api_key="your-api-key-here"
    )

    # Deploy general agent
    agent = client.deploy_agent(
        agent_type=AgentType.GENERAL,
        config={"personality": "helpful and concise"}
    )

    print("Chatbot ready! Type 'quit' to exit.\n")

    try:
        while True:
            user_input = input("You: ")

            if user_input.lower() in ['quit', 'exit', 'bye']:
                break

            response = agent.send(user_input)
            print(f"Bot: {response}\n")

    finally:
        agent.delete()
        client.close()
        print("Chatbot session ended.")


def error_handling_example():
    """Example showing proper error handling"""

    print("\n=== Error Handling Example ===\n")

    client = AgentClient(
        base_url="https://api.aaas.wilbtc.com",
        api_key="your-api-key-here"
    )

    agent = None

    try:
        # Deploy agent
        agent = client.deploy_agent(agent_type=AgentType.CODE)
        print("✓ Agent deployed\n")

        # Use agent with timeout handling
        try:
            response = agent.send("Write a complex algorithm", timeout=30)
            print(f"Response: {response}")

        except TimeoutError:
            print("⚠ Request timed out, retrying with longer timeout...")
            response = agent.send("Write a simple function", timeout=60)
            print(f"Response: {response}")

    except Exception as e:
        print(f"✗ Error: {e}")

    finally:
        # Always cleanup
        if agent:
            agent.delete()
            print("\n✓ Agent cleaned up")

        client.close()


if __name__ == "__main__":
    # Run main example
    main()

    # Uncomment to try other examples:
    # simple_chatbot_example()
    # error_handling_example()

    print("\n" + "="*50)
    print("Want to try this yourself?")
    print("1. pip install aaas-client")
    print("2. Get API key: https://t.me/wilbtc")
    print("3. Replace 'your-api-key-here' with your actual key")
    print("="*50)
