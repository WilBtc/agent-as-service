"""
Basic usage example for Agent as a Service
Demonstrates the new agent types feature with Claude Agent SDK
"""

from aaas import AgentClient, AgentType

# Initialize the client
client = AgentClient(api_key="your-api-key")

print("=== Agent as a Service - Basic Usage ===\n")

# List available agent types
print("Available Agent Types:")
agent_types = client.list_agent_types()
for type_name, type_info in agent_types.items():
    print(f"  - {type_name}: {type_info['description']}")
print()

# Deploy a customer support agent using the new AgentType enum
print("Deploying a customer support agent...")
agent = client.deploy_agent(
    agent_type=AgentType.CUSTOMER_SUPPORT,
    config={
        "language": "en",
        "personality": "professional",
        "permission_mode": "ask"
    }
)

print(f"Agent deployed: {agent.id}")
print(f"Endpoint: {agent.endpoint}")
print()

# Send a message to the agent
print("Sending message to agent...")
response = agent.send("Hello, I need help with my order")
print(f"Agent response: {response}\n")

# Get agent info
info = agent.info()
print(f"Agent status: {info.status}")
print(f"Messages processed: {info.messages_count}")
print()

# Quick query without managing agent lifecycle
print("Using quick query for a research task...")
quick_response = client.quick_query(
    "What are the key features of Claude Agent SDK?",
    agent_type=AgentType.RESEARCH
)
print(f"Quick query response: {quick_response}\n")

# List all agents
all_agents = client.list_agents()
print(f"Total agents: {len(all_agents)}")

# Stop the agent
print("Stopping agent...")
agent.stop()

# Delete the agent
print("Deleting agent...")
agent.delete()

print("Done!")

# Close the client
client.close()
