# MVP Checklist

## Core Goals
- [x] LLM connected via OpenAI-compatible API
- [x] CLI chat interface (send prompt, receive response)
- [x] Tool calling enabled (model can call tools)
- [x] SQLite checkpointing (persist state)

## Test Prompts (for comparison)
- [x] Simple task: "What is 2+2?" (sanity check)
- [x] Code task: "Write a hello world in Python"
- [x] Multi-step: "Create a file hello.py, run it, show output"
- [x] Error recovery: "Fix the syntax error in hello.py" (via retry)

## Configuration
- [x] config.toml with feature flags
- [x] Load config at runtime
- [x] Toggle features on/off

## Verification
- [x] Run test prompts with features OFF
- [x] Run test prompts with feature ON
- [x] Compare results
