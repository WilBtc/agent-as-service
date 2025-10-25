"""
Claude Agent SDK API Verification Report

Date: 2025-10-25
Status: ✅ VERIFIED - FIXES REQUIRED

## Actual API vs Current Implementation

### Current Implementation Issues

Our code in `agent_manager.py` uses:
```python
from claude_agent_sdk import ClaudeSDKClient, query
from claude_agent_sdk.models import ClaudeAgentOptions, AssistantMessage, UserMessage

agent_options = ClaudeAgentOptions(
    cwd=self.working_dir,
    system_prompt=...,
    allowed_tools=...,
    permission_mode=agent_type_config.get("permission_mode").value,  # ❌ WRONG
    max_turns=...,
    model=...  # ❌ NOT SUPPORTED
)

self.client = ClaudeSDKClient(
    api_key=settings.claude_api_key,  # ❌ WRONG
    options=agent_options,
)

async for response_message in self.client.send_message(user_message):  # ❌ WRONG METHOD
```

### Actual SDK API

Correct usage:
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query

options = ClaudeAgentOptions(
    cwd=self.working_dir,  # ✅ String or Path
    system_prompt=...,  # ✅ Correct
    allowed_tools=...,  # ✅ List of strings
    permission_mode='acceptEdits',  # ✅ String, not enum
    max_turns=...,  # ✅ Correct
    # NO model parameter - model is set globally
)

# API key via environment variable ANTHROPIC_API_KEY
async with ClaudeSDKClient(options=options) as client:  # ✅ Context manager
    await client.query("prompt")  # ✅ Use query()
    async for msg in client.receive_response():  # ✅ Use receive_response()
        print(msg)
```

## Key Differences

| Feature | Our Code | Actual API | Fix Required |
|---------|----------|------------|--------------|
| Import path | `claude_agent_sdk.models` | `claude_agent_sdk` | ✅ YES |
| ClaudeAgentOptions.model | Passed as parameter | Not supported | ✅ YES - Remove |
| ClaudeSDKClient.api_key | Constructor parameter | Environment variable | ✅ YES |
| permission_mode | enum.value | String | ✅ YES |
| Send message | `send_message()` | `query()` + `receive_response()` | ✅ YES |
| Context manager | Not used | Required | ✅ YES |
| Message types | AssistantMessage, UserMessage | Same | ✅ OK |

## API Key Handling

**Actual behavior:** Claude Agent SDK reads ANTHROPIC_API_KEY from environment.

Our current code tries to pass it to constructor - this won't work.

**Fix:**
```python
# Set environment variable before creating client
import os
os.environ["ANTHROPIC_API_KEY"] = settings.claude_api_key

# Then create client without api_key parameter
async with ClaudeSDKClient(options=options) as client:
    ...
```

## Message Flow

**Current (WRONG):**
```python
user_message = UserMessage(content=message)
async for response_message in self.client.send_message(user_message):
    ...
```

**Correct:**
```python
await client.query(message)  # Send query
async for response_message in client.receive_response():  # Receive responses
    ...
```

## Prerequisites

The SDK requires:
- Python 3.10+
- Node.js
- Claude Code 2.0.0+: `npm install -g @anthropic-ai/claude-code`
- ANTHROPIC_API_KEY environment variable

## Impact

**CRITICAL:** Current implementation will fail at runtime because:
1. ClaudeAgentOptions doesn't accept `model` parameter → AttributeError
2. ClaudeSDKClient doesn't accept `api_key` parameter → TypeError
3. `send_message()` method doesn't exist → AttributeError
4. Import from `.models` will fail → ImportError

## Fixes Required

1. ✅ Update imports
2. ✅ Remove `model` parameter from ClaudeAgentOptions
3. ✅ Set ANTHROPIC_API_KEY via environment
4. ✅ Use context manager pattern
5. ✅ Replace send_message() with query() + receive_response()
6. ✅ Convert permission_mode enum to string

## Corrected Implementation

See: `src/aaas/agent_manager_fixed.py`

## Testing

After fixes, test with:
```python
pytest tests/test_claude_sdk_integration.py
```

## References

- Official Docs: https://docs.claude.com/en/api/agent-sdk/python
- GitHub: https://github.com/anthropics/claude-agent-sdk-python
- PyPI: https://pypi.org/project/claude-agent-sdk/
