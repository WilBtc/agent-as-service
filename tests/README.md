# AaaS Test Suite

Comprehensive test suite for Agent as a Service (AaaS) platform.

## Test Coverage

### 1. Agent Type Tests (`test_agent_types.py`)
- **Purpose**: Validate agent type configurations and specializations
- **Coverage**: 20+ test methods across 3 test classes
- **Tests**:
  - Agent type configuration validation
  - Tool access restrictions (security)
  - Permission mode configurations
  - Specialized agent capabilities
  - Configuration overrides
  - Backward compatibility

### 2. API Endpoint Tests (`test_api_endpoints.py`)
- **Purpose**: Test FastAPI REST API endpoints
- **Coverage**: 40+ test methods across 8 test classes
- **Tests**:
  - Root and health endpoints
  - Authentication (valid/invalid/missing API keys)
  - Agent CRUD operations
  - Agent lifecycle operations (start/stop)
  - Message sending
  - Quick query endpoint
  - Rate limiting
  - Error handling
  - Full integration workflows

### 3. Agent Manager Tests (`test_agent_manager.py`)
- **Purpose**: Test agent management and core agent functionality
- **Coverage**: 30+ test methods across 5 test classes
- **Tests**:
  - Agent creation with different types
  - Agent lifecycle management
  - Max agents limit enforcement
  - Quick query functionality
  - Message sending and context handling
  - Error handling
  - Concurrent operations
  - Agent status transitions

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run all tests with verbose output
pytest -v

# Run with detailed coverage report
pytest --cov=src/aaas --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only API tests
pytest -m api

# Run only authentication tests
pytest -m auth

# Run only rate limiting tests
pytest -m rate_limit

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Run Specific Test Files

```bash
# Run agent type tests only
pytest tests/test_agent_types.py

# Run API endpoint tests only
pytest tests/test_api_endpoints.py

# Run agent manager tests only
pytest tests/test_agent_manager.py
```

### Run Specific Test Classes or Methods

```bash
# Run specific test class
pytest tests/test_agent_types.py::TestAgentTypeConfigurations

# Run specific test method
pytest tests/test_agent_types.py::TestAgentTypeConfigurations::test_all_agent_types_have_configs

# Run tests matching a pattern
pytest -k "customer_support"
```

## Test Configuration

### pytest.ini
Main pytest configuration file with:
- Test discovery patterns
- Coverage settings
- Asyncio configuration
- Test markers
- Logging configuration

### conftest.py
Shared fixtures and configuration:
- Mock Claude SDK client
- Mock agents
- Authentication helpers
- Environment variable mocking
- Cleanup utilities

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for multiple components
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.rate_limit` - Rate limiting tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.asyncio` - Async tests (automatically applied)

## Coverage Reports

After running tests with coverage:

```bash
# Generate HTML coverage report
pytest --cov=src/aaas --cov-report=html

# Open the report in browser
open htmlcov/index.html
```

Coverage reports show:
- Line coverage percentage
- Branch coverage
- Missing lines
- Excluded lines

## Writing New Tests

### Test Structure

```python
import pytest
from aaas.models import AgentConfig, AgentType

class TestFeature:
    """Test a specific feature"""

    @pytest.mark.asyncio
    async def test_something(self, sample_agent_config):
        """Test description"""
        # Arrange
        config = sample_agent_config

        # Act
        result = await some_function(config)

        # Assert
        assert result is not None
```

### Using Fixtures

```python
def test_with_auth(self, enable_auth):
    """Test with authentication enabled"""
    api_key = enable_auth  # Returns test API key
    # Your test code

def test_without_auth(self, disable_auth):
    """Test without authentication"""
    # Your test code
```

### Mocking Claude SDK

```python
@pytest.mark.asyncio
async def test_with_claude_sdk(self, mock_claude_client):
    """Test with mocked Claude SDK"""
    # mock_claude_client is already configured
    # Just patch where it's used
    with patch("aaas.agent_manager.ClaudeSDKClient") as mock:
        mock.return_value = mock_claude_client
        # Your test code
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov
    pytest --cov=src/aaas --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use fixtures to clean up resources after tests
3. **Mocking**: Mock external dependencies (Claude SDK, file system, etc.)
4. **Async**: Use `@pytest.mark.asyncio` for async tests
5. **Naming**: Use descriptive test names that explain what is being tested
6. **Documentation**: Add docstrings to test classes and methods
7. **Markers**: Use appropriate markers to categorize tests
8. **Assertions**: Use clear, specific assertions with helpful error messages

## Troubleshooting

### Import Errors

```bash
# Make sure src/ is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
pytest
```

### Async Warnings

If you see warnings about asyncio:
- Ensure `pytest-asyncio` is installed
- Check `pytest.ini` has `asyncio_mode = auto`
- Use `@pytest.mark.asyncio` on async tests

### Coverage Not Working

```bash
# Install coverage dependencies
pip install pytest-cov coverage

# Run with explicit coverage options
pytest --cov=src/aaas --cov-report=term-missing
```

## Next Steps

### Additional Tests Needed

1. **Load Testing**
   - Multi-agent concurrent operations
   - High-volume message sending
   - Memory usage under load
   - Connection pool management

2. **Security Testing**
   - SQL injection attempts
   - API key brute force
   - Rate limit bypass attempts
   - Permission escalation

3. **Edge Cases**
   - Network failures
   - Timeout handling
   - Malformed requests
   - Resource exhaustion

4. **Performance Testing**
   - Response time benchmarks
   - Throughput measurements
   - Resource utilization

## Support

For questions or issues with tests:
1. Check test documentation above
2. Review conftest.py for available fixtures
3. Check pytest.ini for configuration
4. Open an issue on GitHub

## License

Same as main project license (see LICENSE file in project root).
