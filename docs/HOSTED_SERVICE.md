# AaaS Hosted Service - Quick Start

Welcome to **Agent as a Service (AaaS)** hosted service! This guide will help you get started with our managed AI agent platform in minutes - no infrastructure setup required.

## 🚀 What is AaaS Hosted Service?

AaaS Hosted Service is a fully managed, cloud-based platform that provides instant access to specialized AI agents. We handle all the infrastructure, scaling, and maintenance - you just focus on using the agents to power your applications.

### ✨ Benefits of Hosted Service

- **Zero Infrastructure** - No servers, no setup, no maintenance
- **Instant Availability** - Get started in under 2 minutes
- **Auto-Scaling** - Scale from 1 to 1000+ agents automatically
- **99.9% Uptime** - Enterprise-grade reliability
- **Global CDN** - Low latency worldwide
- **Managed Updates** - Always on the latest version
- **24/7 Support** - Expert support via Telegram

## 📦 Installation

### Step 1: Install the Client Library

Simply install the AaaS client library using pip:

```bash
pip install aaas-client
```

That's it! No need to install Claude Code, set up servers, or configure infrastructure.

### Step 2: Get Your API Key

1. Contact us on Telegram: [@wilbtc](https://t.me/wilbtc)
2. Request access to AaaS Hosted Service
3. Receive your API key and service URL

## 🎯 Quick Start Example

Here's a complete example to deploy and use an agent in less than 10 lines of code:

```python
from aaas import AgentClient, AgentType

# Connect to AaaS Hosted Service
client = AgentClient(
    base_url="https://api.aaas.wilbtc.com",  # Our hosted service URL
    api_key="your-api-key-here"
)

# Deploy a research agent
agent = client.deploy_agent(agent_type=AgentType.RESEARCH)

# Use it immediately
response = agent.send("Research the latest trends in AI agents")
print(response)

# Clean up
agent.delete()
```

## 🤖 Available Agent Types

All specialized agent types are available in the hosted service:

### 1. Research Agent
Perfect for comprehensive research and analysis:
```python
research_agent = client.deploy_agent(
    agent_type=AgentType.RESEARCH,
    config={
        "max_tokens": 8192,
        "temperature": 0.7
    }
)
```

### 2. Code Agent
Ideal for development tasks:
```python
code_agent = client.deploy_agent(
    agent_type=AgentType.CODE,
    config={
        "temperature": 0.5,
        "permission_mode": "acceptEdits"
    }
)
```

### 3. Customer Support Agent
For customer service automation:
```python
support_agent = client.deploy_agent(
    agent_type=AgentType.CUSTOMER_SUPPORT,
    config={
        "personality": "friendly",
        "language": "en"
    }
)
```

### 4. Finance Agent
For financial analysis:
```python
finance_agent = client.deploy_agent(
    agent_type=AgentType.FINANCE,
    config={
        "temperature": 0.3
    }
)
```

### 5. Data Analysis Agent
For data insights:
```python
data_agent = client.deploy_agent(
    agent_type=AgentType.DATA_ANALYSIS,
    config={
        "max_tokens": 8192
    }
)
```

## 💡 Common Use Cases

### One-Off Queries (No Agent Management)

For simple queries without managing agent lifecycle:

```python
from aaas import AgentClient, AgentType

client = AgentClient(
    base_url="https://api.aaas.wilbtc.com",
    api_key="your-api-key"
)

# Quick query - no agent creation needed
response = client.quick_query(
    "Analyze this business proposal...",
    agent_type=AgentType.RESEARCH
)
print(response)
```

### Long-Running Conversations

For interactive conversations with context:

```python
# Deploy a persistent agent
agent = client.deploy_agent(agent_type=AgentType.GENERAL)

# Have multiple interactions
response1 = agent.send("What are the benefits of AI?")
response2 = agent.send("Can you elaborate on the first point?")
response3 = agent.send("How does this apply to healthcare?")

# Agent maintains conversation context
agent.delete()
```

### Multi-Agent Workflow

Orchestrate multiple specialized agents:

```python
# Create specialized agents
research = client.deploy_agent(agent_type=AgentType.RESEARCH)
code = client.deploy_agent(agent_type=AgentType.CODE)
data = client.deploy_agent(agent_type=AgentType.DATA_ANALYSIS)

# Use them in a workflow
findings = research.send("Research best practices for API design")
implementation = code.send(f"Implement an API based on: {findings}")
metrics = data.send("Analyze API performance metrics")

# Cleanup
research.delete()
code.delete()
data.delete()
```

## 🔧 Configuration Options

### Client Configuration

```python
client = AgentClient(
    base_url="https://api.aaas.wilbtc.com",
    api_key="your-api-key",
    timeout=120.0  # Request timeout in seconds
)
```

### Agent Configuration

```python
from aaas import PermissionMode

agent = client.deploy_agent(
    agent_type=AgentType.CODE,
    config={
        # Model configuration
        "model": "claude-sonnet-4-5-20250929",
        "temperature": 0.7,
        "max_tokens": 8192,

        # Agent behavior
        "permission_mode": PermissionMode.ACCEPT_EDITS,
        "system_prompt": "Custom instructions for the agent",

        # Tool access
        "allowed_tools": ["Read", "Write", "Grep", "Bash"],

        # Conversation limits
        "max_turns": 50,

        # Localization
        "language": "en",
        "personality": "professional"
    },
    auto_start=True  # Start immediately
)
```

## 📊 Monitoring & Management

### List All Your Agents

```python
# Get all active agents
agents = client.list_agents()

for agent_id, info in agents.items():
    print(f"Agent: {agent_id}")
    print(f"  Type: {info.config.agent_type}")
    print(f"  Status: {info.status}")
    print(f"  Messages: {info.messages_count}")
```

### Check Service Health

```python
# Health check
health = client.health_check()
print(f"Status: {health['status']}")
print(f"Active agents: {health['agents_count']}")
print(f"Capacity: {health['max_agents']}")
```

### Discover Agent Types

```python
# List available agent types and their capabilities
types = client.list_agent_types()

for type_name, type_info in types.items():
    print(f"{type_name}:")
    print(f"  Description: {type_info['description']}")
    print(f"  Tools: {type_info['allowed_tools']}")
```

## 💰 Pricing & Plans

### Free Tier
- 100 agent-hours/month
- All agent types
- Basic support
- Perfect for testing and small projects

### Professional
- 1,000 agent-hours/month
- Priority support
- Custom agent configurations
- SLA: 99.9% uptime

### Enterprise
- Unlimited agents
- 24/7 dedicated support
- Custom SLA
- Private deployment options
- Advanced analytics

**Contact:** [@wilbtc](https://t.me/wilbtc) on Telegram for pricing details.

## 🔒 Security & Privacy

- **Encrypted Communication** - All API calls use TLS 1.3
- **Data Isolation** - Your agents and data are completely isolated
- **No Data Retention** - We don't store your conversation data
- **Compliance** - SOC 2, GDPR, HIPAA compliant
- **API Key Management** - Rotate keys anytime via dashboard

## 📚 Best Practices

### 1. Use Context Managers

```python
with AgentClient(base_url="...", api_key="...") as client:
    agent = client.deploy_agent(agent_type=AgentType.RESEARCH)
    response = agent.send("Query here")
    agent.delete()
# Client automatically closed
```

### 2. Handle Errors Gracefully

```python
try:
    agent = client.deploy_agent(agent_type=AgentType.CODE)
    response = agent.send("Write a function...")
except Exception as e:
    print(f"Error: {e}")
finally:
    if agent:
        agent.delete()
```

### 3. Clean Up Resources

Always delete agents when done to avoid charges:

```python
agents = []
try:
    # Create agents
    agents.append(client.deploy_agent(AgentType.RESEARCH))
    agents.append(client.deploy_agent(AgentType.CODE))

    # Use agents...

finally:
    # Clean up
    for agent in agents:
        agent.delete()
```

### 4. Use Quick Queries for Simple Tasks

For one-off queries, use quick_query to avoid agent management:

```python
# More efficient for single queries
response = client.quick_query(
    "Quick question here",
    agent_type=AgentType.GENERAL
)
```

## 🆘 Support

### Getting Help

- **Telegram:** [@wilbtc](https://t.me/wilbtc) - Direct message for support
- **Email:** support@wilbtc.com
- **Status Page:** https://status.aaas.wilbtc.com
- **Documentation:** https://docs.aaas.wilbtc.com

### Common Issues

**"Invalid API key"**
- Verify your API key is correct
- Check if key has expired
- Contact support to rotate key

**"Agent limit reached"**
- Check your plan's agent limits
- Delete unused agents
- Upgrade your plan

**"Request timeout"**
- Increase client timeout: `AgentClient(timeout=180)`
- Check your internet connection
- Contact support if issue persists

## 🚀 What's Next?

1. **Explore Examples** - Check out `/examples` directory for more code samples
2. **Read API Docs** - Full API reference at https://docs.aaas.wilbtc.com
3. **Join Community** - Connect with other users on Telegram
4. **Upgrade Plan** - Scale up as your needs grow

## 📝 Example: Complete Application

Here's a complete example building a customer service bot:

```python
from aaas import AgentClient, AgentType
import time

def customer_service_bot():
    """Simple customer service bot using AaaS"""

    # Initialize
    client = AgentClient(
        base_url="https://api.aaas.wilbtc.com",
        api_key="your-api-key"
    )

    # Deploy support agent
    agent = client.deploy_agent(
        agent_type=AgentType.CUSTOMER_SUPPORT,
        config={
            "personality": "friendly",
            "language": "en"
        }
    )

    print("Customer Service Bot Ready!")
    print("Type 'quit' to exit\n")

    try:
        while True:
            # Get user input
            user_input = input("You: ")

            if user_input.lower() == 'quit':
                break

            # Get response from agent
            response = agent.send(user_input)
            print(f"Bot: {response}\n")

    finally:
        # Cleanup
        agent.delete()
        client.close()
        print("Session ended")

if __name__ == "__main__":
    customer_service_bot()
```

---

**Ready to get started?** Contact [@wilbtc](https://t.me/wilbtc) on Telegram to get your API key and begin using AaaS Hosted Service today!
