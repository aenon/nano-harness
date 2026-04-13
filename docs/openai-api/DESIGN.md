# OpenAI API Server Design

## Overview
Expose nano-harness as an OpenAI-compatible API endpoint.

## Specification

### Endpoint
```
POST /v1/chat/completions
```

### Parameters to Support

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| `model` | Yes | - | Currently ignored, uses config |
| `messages` | Yes | - | Array of message objects |
| `temperature` | No | config default | 0.0-2.0 |
| `max_tokens` | No | 4096 | |
| `tools` | No | None | Function calling |
| `stream` | No | false | Not implemented |

### Request Format
```json
{
  "model": "nemotron-3-nano-30b-a3b",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7
}
```

### Response Format
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "nemotron-3-nano-30b-a3b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

## Gaps to Address

1. **Server**: No HTTP server exists - need to create with FastAPI
2. **Message conversion**: OpenAI format differs from our internal format
3. **Tool handling**: Need to convert OpenAI tool schema to our format
4. **Response format**: Need to convert our response to OpenAI format
5. **Config loading**: Need to support loading from env for API mode

## Current Status

### Implemented
- Basic OpenAI-compatible endpoint at `/v1/chat/completions`
- Health check at `/health`
- Supports: messages, model, temperature, max_tokens, tools

### Not Implemented (TODO)
- Multi-step planning via API
- Judge self-verification via API
- Streaming responses
- Auth

### Next Steps
1. Test with OpenCode or similar tool
2. Add planning/judge support
3. Consider streaming