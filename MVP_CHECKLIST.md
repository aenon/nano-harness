# MVP Checklist

## Core Goals
- [ ] LLM connected via OpenAI-compatible API
- [ ] CLI chat interface (send prompt, receive response)
- [ ] Tool calling enabled (model can call tools)
- [ ] SQLite checkpointing (persist state)

## Test Prompts (for comparison)
- [ ] Simple task: "What is 2+2?" (sanity check)
- [ ] Code task: "Write a hello world in Python"
- [ ] Multi-step: "Create a file hello.py, run it, show output"
- [ ] Error recovery: "Fix the syntax error in hello.py"

## Configuration
- [ ] config.toml with feature flags
- [ ] Load config at runtime
- [ ] Toggle features on/off

## Verification
- [ ] Run test prompts with features OFF
- [ ] Run test prompts with feature ON
- [ ] Compare results
