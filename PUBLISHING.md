# Publishing AaaS Client to PyPI

This guide explains how to publish the `aaas-client` package to PyPI so customers can install it with `pip install aaas-client`.

## Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org
   - Create account at https://test.pypi.org (for testing)

2. **Install Publishing Tools**
   ```bash
   pip install build twine
   ```

3. **Create API Tokens**
   - Go to https://pypi.org/manage/account/token/
   - Create a token named "aaas-client"
   - Save the token securely

## Publishing Steps

### 1. Test the Package Locally

```bash
# Build the client package
python setup-client.py sdist bdist_wheel

# Check the distribution
twine check dist/*

# Test installation locally
pip install dist/aaas_client-2.0.0-py3-none-any.whl
```

### 2. Test on TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ aaas-client
```

### 3. Publish to PyPI

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build fresh
python setup-client.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

### 4. Verify Installation

```bash
# Test installation
pip install aaas-client

# Verify it works
python -c "from aaas import AgentClient, AgentType; print('Success!')"
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish-client.yml`:

```yaml
name: Publish Client to PyPI

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install build twine

      - name: Build client package
        run: |
          python setup-client.py sdist bdist_wheel

      - name: Check package
        run: |
          twine check dist/*

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          twine upload dist/*
```

Add your PyPI token as a GitHub secret named `PYPI_API_TOKEN`.

## Version Management

### Updating Version

1. Update version in `setup-client.py`:
   ```python
   version="2.1.0",
   ```

2. Update version in `pyproject.toml`:
   ```toml
   version = "2.1.0"
   ```

3. Update version in `src/aaas/__init__.py`:
   ```python
   __version__ = "2.1.0"
   ```

4. Update CHANGELOG.md with changes

5. Create git tag:
   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```

## Package Structure

The client package includes:
- `src/aaas/` - Core client library
  - `client.py` - AgentClient class
  - `models.py` - Data models (AgentType, PermissionMode, etc.)
  - `__init__.py` - Package exports
- `CLIENT_README.md` - Client package README
- `docs/HOSTED_SERVICE.md` - Hosted service documentation
- `examples/hosted_service_example.py` - Usage examples

## What's NOT Included in Client Package

The client package excludes server components:
- `agent_manager.py` - Server-side agent management
- `api.py` - FastAPI server
- `server.py` - Server startup
- `cli.py` - CLI commands
- `claude-agent-sdk` dependency
- Docker files
- Tests

Customers only get the lightweight client library.

## Maintenance

### Regular Updates

1. Update dependencies:
   ```bash
   pip-compile setup-client.py --output-file requirements-client.txt
   ```

2. Test with new Python versions

3. Monitor PyPI statistics at https://pypi.org/project/aaas-client/

### Support

- Monitor GitHub issues
- Respond to PyPI package inquiries
- Update docs based on feedback

## Marketing

Once published, promote:
1. Update README.md with PyPI badge
2. Announce on social media
3. Create tutorial videos
4. Write blog posts
5. Submit to package indexes

## Troubleshooting

**"Package already exists"**
- You can't overwrite published versions
- Increment version number and republish

**"Authentication failed"**
- Check your PyPI token
- Ensure token has upload permissions
- Try re-creating the token

**"Package files invalid"**
- Run `twine check dist/*`
- Fix any warnings or errors
- Rebuild and retry

## Quick Reference

```bash
# Complete publishing workflow
rm -rf build/ dist/ *.egg-info/
python setup-client.py sdist bdist_wheel
twine check dist/*
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*  # Production
```

## Customer Installation

Once published, customers can install with:

```bash
# Simple install
pip install aaas-client

# Specific version
pip install aaas-client==2.0.0

# Upgrade
pip install --upgrade aaas-client

# One-line installer (Linux/Mac)
curl -sSL https://raw.githubusercontent.com/WilBtc/agent-as-service/main/install-client.sh | bash

# One-line installer (Windows)
iwr -useb https://raw.githubusercontent.com/WilBtc/agent-as-service/main/install-client.ps1 | iex
```
