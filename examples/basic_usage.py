"""
Basic usage example for Agent as a Service
"""

from aaas import AgentClient

# Initialize the client
client = AgentClient(api_key="your-api-key")

# Deploy a customer service agent
agent = client.deploy_agent(
    template="customer-service-pro",
    config={
        "language": "en",
        "integration": "zendesk",
        "personality": "professional"
    }
)

print(f"Agent deployed: {agent.id}")
print(f"Endpoint: {agent.endpoint}")

# Send a message to the agent
response = agent.send("Hello, I need help with my order")
print(f"Agent response: {response}")

# Get agent info
info = agent.info()
print(f"Agent status: {info.status}")
print(f"Messages processed: {info.messages_count}")

# List all agents
all_agents = client.list_agents()
print(f"Total agents: {len(all_agents)}")

# Stop the agent
agent.stop()

# Delete the agent
agent.delete()

# Close the client
client.close()
