# AaaS Client - Connect to Hosted Service

Simple Python client for **Agent as a Service (AaaS)** hosted platform. Deploy and manage specialized AI agents in seconds.

## ⚡ Quick Install

```bash
pip install aaas-client
```

**That's it!** No infrastructure setup required.

## 🚀 Get Started in 30 Seconds

```python
from aaas import AgentClient, AgentType

# Connect to hosted service
client = AgentClient(
    base_url="https://api.aaas.wilbtc.com",
    api_key="your-api-key-here"
)

# Deploy a specialized agent
agent = client.deploy_agent(agent_type=AgentType.RESEARCH)

# Use it immediately
response = agent.send("Research the latest AI trends")
print(response)

# Clean up
agent.delete()
```

## 🤖 Available Agent Types

- **RESEARCH** - Deep research and comprehensive analysis
- **CODE** - Code development, review, and debugging
- **FINANCE** - Financial analysis and portfolio management
- **CUSTOMER_SUPPORT** - Customer service automation
- **PERSONAL_ASSISTANT** - Productivity and task management
- **DATA_ANALYSIS** - Data analysis and insights
- **GENERAL** - General-purpose tasks

## 💡 Simple Examples

### Quick Query (No Agent Management)

```python
# One-line query without managing lifecycle
response = client.quick_query(
    "Analyze this business proposal...",
    agent_type=AgentType.RESEARCH
)
```

### Interactive Conversation

```python
agent = client.deploy_agent(agent_type=AgentType.GENERAL)

# Agent remembers context
agent.send("What are the benefits of AI?")
agent.send("Can you elaborate on point 2?")
agent.send("How does this apply to healthcare?")

agent.delete()
```

### Multi-Agent Workflow

```python
# Use multiple specialized agents
research = client.deploy_agent(agent_type=AgentType.RESEARCH)
code = client.deploy_agent(agent_type=AgentType.CODE)

findings = research.send("Research best API practices")
implementation = code.send(f"Implement API: {findings}")

research.delete()
code.delete()
```

## 🔑 Getting Your API Key

**Contact us on Telegram:** [@wilbtc](https://t.me/wilbtc)

We'll set you up with:
- API key
- Service URL
- Free tier to start (100 agent-hours/month)

## 📚 Documentation

- **Full Guide:** [docs/HOSTED_SERVICE.md](docs/HOSTED_SERVICE.md)
- **Examples:** [examples/](examples/)
- **Support:** [@wilbtc](https://t.me/wilbtc) on Telegram

## 💰 Pricing

**Free Tier:** 100 agent-hours/month
**Professional:** 1,000 agent-hours/month
**Enterprise:** Unlimited agents + dedicated support

Contact [@wilbtc](https://t.me/wilbtc) for details.

## 🔒 Security

- TLS 1.3 encrypted
- No data retention
- GDPR & HIPAA compliant
- Data isolation per customer

## 🆘 Support

- **Telegram:** [@wilbtc](https://t.me/wilbtc)
- **Email:** support@wilbtc.com

---

**Ready?** Install now and get your API key:

```bash
pip install aaas-client
```

Then contact [@wilbtc](https://t.me/wilbtc) to activate your account!
