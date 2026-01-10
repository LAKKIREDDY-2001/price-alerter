# LiteLLM OpenRouter Error Fix Plan

## Error Summary

```
400 litellm.BadRequestError: OpenrouterException - {
  "error": {
    "message": "Provider returned error",
    "code": 400,
    "metadata": {
      "raw": "invalid params, tool result's tool id(call_function_9asz0ztseet5_2) not found (2013)"
    }
  }
}
```

**Root Cause:** The MCP (Model Context Protocol) server tried to reference a tool call result with ID `call_function_9asz0ztseet5_2` that doesn't exist or has expired.

---

## Immediate Solutions

### Option 1: Update Model Configuration

Update your LiteLLM config to use stable, well-tested models:

```python
# litellm_config.py
import litellm

# Recommended model configuration
model_configs = {
    "openrouter/minimax-m2": {
        "enabled": False  # Disable problematic model
    },
    "custom/blackbox-base": {
        "model_list": [
            {
                "model_name": "gpt-4.1-mini",
                "litellm_params": {
                    "model": "openai/gpt-4o-mini",
                    "api_key": "your-api-key"
                }
            }
        ]
    }
}

# Safe fallback configuration
litellm.set_verbose = False
litellm.cache = None  # Disable caching to avoid stale tool IDs
```

### Option 2: Disable Fallback Chain (Simpler Fix)

```python
import litellm

# Disable automatic fallbacks
litellm.disable_retries = True

# Or set max retries to 0
litellm.max_retries = 0
```

### Option 3: Complete LiteLLM Configuration

Create a proper `litellm_config.yaml`:

```yaml
model_list:
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENROUTER_API_KEY
      base_url: https://openrouter.ai/api/v1
    model_info:
      mode_group: openrouter/openai

  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings: 
  master_key: os.environ/LITELLM_LICENSE_KEY

litellm_settings:
  cache_params: False
  drop_params: True
  add_params: {}

completion_model: openai/gpt-4o-mini
```

---

## VSCode Settings (Blackbox AI / MCP)

If you're using VSCode with Blackbox AI or similar extension:

1. **Open VSCode Settings** (`Cmd + ,`)
2. **Search for:** `MCP` or `litellm`
3. **Update configuration:**

```json
{
  "mcpServers": {
    "custom-server": {
      "command": "python",
      "args": ["/path/to/mcp-server.py"],
      "env": {
        "LITELLM_LOG": "ERROR",
        "OPENROUTER_API_KEY": "your-key-here"
      }
    }
  },
  "blackboxai.apiKeys": {
    "openrouter": "your-openrouter-key"
  }
}
```

---

## Environment Variables (.env)

Create or update your `.env` file:

```bash
# LiteLLM Configuration
LITELLM_LOG_LEVEL=ERROR
LITELLM_CACHE=False
LITELLM_DISABLE_RETRIES=True
LITELLM_MAX_RETRIES=0

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-your-api-key

# Disable problematic models
DISABLE_MINIMAX=true
```

---

## Python Code Fix

If you're calling LiteLLM directly, update your code:

```python
import litellm
from litellm import completion

# Disable retries to prevent fallback chain issues
litellm.disable_retries = True

# Or configure safe defaults
litellm.set_verbose = False

# Safe completion call
try:
    response = completion(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
        max_retries=0,  # No retries
        api_key="your-api-key"
    )
except Exception as e:
    print(f"Error: {e}")
```

---

## Model Group Configuration Fix

The error shows:
```
No fallback model group found for original model_group=openrouter/minimax-m2
Fallbacks=[{'custom/blackbox-base': ['gpt-4.1-mini']}]
```

**Fix:** Ensure the model group mapping is correct:

```python
import litellm

# Set proper model group mapping
litellm.model_group_map = {
    "openrouter/minimax-m2": ["openrouter/openai/gpt-4o-mini"],
    "custom/blackbox-base": ["openai/gpt-4o-mini"]
}

# Or disable model groups entirely
litellm.use_standard_model_group = False
```

---

## Testing the Fix

Create a test script:

```python
# test_litellm.py
import litellm

def test_completion():
    try:
        response = litellm.completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Test message"}],
            max_retries=0
        )
        print("Success:", response)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_completion()
```

Run with:
```bash
python test_litellm.py
```

---

## Recommended Stable Models

For OpenRouter, these models are well-tested:

1. **openai/gpt-4o-mini** - Fast, cheap, reliable
2. **anthropic/claude-sonnet-4-20250514** - High quality
3. **google/gemini-2.5-pro** - Good reasoning
4. **meta-llama/llama-4-scout** - Open source

Avoid:
- `openrouter/minimax-m2` - Has tool ID issues
- Experimental models without fallback support

---

## Files to Update

1. `~/.env` - Add environment variables
2. VSCode settings.json - Update MCP configuration  
3. `litellm_config.yaml` - Model configuration
4. `requirements.txt` - Add litellm if needed

---

## Quick Fix Command

Run this to apply the quickest fix:

```bash
# Disable retries
export LITELLM_DISABLE_RETRIES=True
export LITELLM_MAX_RETRIES=0
export LITELLM_LOG_LEVEL=ERROR

# Test
python -c "import litellm; litellm.disable_retries=True; print('LiteLLM configured successfully')"
```

