# AaaS Client Installer for Windows
# Usage: iwr -useb https://raw.githubusercontent.com/WilBtc/agent-as-service/main/install-client.ps1 | iex

Write-Host "======================================"
Write-Host "  AaaS Client Installer"
Write-Host "  Agent as a Service - Hosted"
Write-Host "======================================"
Write-Host ""

# Check Python version
Write-Host "Checking Python version..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found $pythonVersion"

    # Check if version is >= 3.10
    $version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ([version]$version -ge [version]"3.10") {
        Write-Host "✓ Python version is compatible"
    } else {
        Write-Host "✗ Error: Python 3.10 or higher required"
        Write-Host "  Current version: $version"
        exit 1
    }
} catch {
    Write-Host "✗ Error: Python not found"
    Write-Host "  Please install Python 3.10 or higher from https://python.org"
    exit 1
}

Write-Host ""

# Install aaas-client
Write-Host "Installing aaas-client..."
try {
    pip install aaas-client
    Write-Host "✓ aaas-client installed successfully"
} catch {
    Write-Host "✗ Error: Installation failed"
    exit 1
}

Write-Host ""
Write-Host "======================================"
Write-Host "  Installation Complete!"
Write-Host "======================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Get your API key:"
Write-Host "   Contact @wilbtc on Telegram: https://t.me/wilbtc"
Write-Host ""
Write-Host "2. Try this example:"
Write-Host ""

$example = @"
from aaas import AgentClient, AgentType

client = AgentClient(
    base_url="https://api.aaas.wilbtc.com",
    api_key="your-api-key-here"
)

agent = client.deploy_agent(agent_type=AgentType.GENERAL)
response = agent.send("Hello!")
print(response)
agent.delete()
"@

Write-Host $example
Write-Host ""
Write-Host "3. Read the docs:"
Write-Host "   https://github.com/WilBtc/agent-as-service/blob/main/docs/HOSTED_SERVICE.md"
Write-Host ""
Write-Host "Need help? Contact @wilbtc on Telegram"
Write-Host ""
