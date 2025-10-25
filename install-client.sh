#!/bin/bash
#
# Quick install script for AaaS Client (Hosted Service)
#
# Usage: curl -sSL https://raw.githubusercontent.com/WilBtc/agent-as-service/main/install-client.sh | bash
#

set -e

echo "======================================"
echo "  AaaS Client Installer"
echo "  Agent as a Service - Hosted"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "✓ Found Python $PYTHON_VERSION"

    # Check if version is >= 3.10
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
        echo "✓ Python version is compatible"
    else
        echo "✗ Error: Python 3.10 or higher required"
        echo "  Current version: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "✗ Error: Python 3 not found"
    echo "  Please install Python 3.10 or higher"
    exit 1
fi

echo ""

# Install aaas-client
echo "Installing aaas-client..."
if pip3 install aaas-client; then
    echo "✓ aaas-client installed successfully"
else
    echo "✗ Error: Installation failed"
    exit 1
fi

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Get your API key:"
echo "   Contact @wilbtc on Telegram: https://t.me/wilbtc"
echo ""
echo "2. Try this example:"
echo ""
cat << 'EOF'
from aaas import AgentClient, AgentType

client = AgentClient(
    base_url="https://api.aaas.wilbtc.com",
    api_key="your-api-key-here"
)

agent = client.deploy_agent(agent_type=AgentType.GENERAL)
response = agent.send("Hello!")
print(response)
agent.delete()
EOF
echo ""
echo "3. Read the docs:"
echo "   https://github.com/WilBtc/agent-as-service/blob/main/docs/HOSTED_SERVICE.md"
echo ""
echo "Need help? Contact @wilbtc on Telegram"
echo ""
