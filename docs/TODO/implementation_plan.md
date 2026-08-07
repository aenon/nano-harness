# Implementation Plan: Remaining TODOs

## Current Status

| Feature | Status |
|---------|--------|
| Subagents | ✅ Implemented (see `nano_harness/subagent.py`) |
| Streaming responses | ❌ Planned |
| Multi-step planning via API | ❌ Planned |
| Judge self-verification via API | ❌ Planned |
| Auth on API server | ❌ Planned |
| Reasoning/thinking mode | ❌ Planned |
| Additional tools beyond shell | ❌ Planned |

---

## 1. Streaming Responses (Server)

**Why**: Long-running tasks (planning + judge + multi-round) block the HTTP response. Streaming lets the client see progress in real-time.

**Approach**: Use Server-Sent Events (SSE) via FastAPI's `StreamingResponse`.

### Changes
- `server.py`: Add `stream=True` support to `/v1/chat/completions`
  - When `stream=True`, yield `ChatCompletionChunk` SSE events
  - Pipe LLM response tokens as they arrive (use OpenAI SDK streaming)
  - Each event: `data: {"choices": [{"delta": {"content": "..."}}]}`
  - Final event: `data: {"choices": [{"finish_reason": "stop"}]}`
- `client.py`: Add `chat_stream()` method that yields tokens from the OpenAI streaming API
- No new dependencies — FastAPI already has `StreamingResponse`

### Complexity: Low
### Risk: Low — standard pattern, well-documented

---

## 2. Multi-Step Planning via API

**Why**: The CLI supports planning, but the API server only does single-step chat. Tools like OpenCode need planning over the API.

**Approach**: Wire the existing `_run_with_planning()` logic into the server. The cleanest route is to refactor the planning logic out of `cli.py` into a shared module.

### Changes
- **New file `nano_harness/engine.py`**: Extract execution logic (`_run_simple`, `_run_with_planning`, `_run_with_judge`, `_execute_step`) from `cli.py` into reusable functions
  - Return structured results instead of `click.echo()`
  - Accept callbacks for progress reporting (used by CLI for display, by server for SSE streaming)
- `server.py`: When `?planning=true` query param is set, call engine with planning enabled
  - For non-streaming: run synchronously, return full result
  - For streaming: yield step progress via SSE
- `cli.py`: Slim down to just argument parsing + display, delegating to `engine.py`

### Key Design Decision
The engine should be **display-agnostic**:
```python
class ExecutionResult:
    task: str
    steps: list[StepResult]
    final_output: str
    success: bool
    rounds: int

def run_task(config, task, messages, planning=False, judge=False, on_progress=None):
    ...
```

### Complexity: Medium — requires refactoring cli.py without breaking CLI
### Risk: Medium — cli.py is the biggest file; need to be careful

---

## 3. Judge Self-Verification via API

**Why**: Same as planning — judge works in CLI but not exposed via API.

**Approach**: Trivial once engine.py is extracted. Add `?judge=true&criteria=...` query params.

### Changes
- `engine.py`: Same refactoring as above handles this
- `server.py`: Wire `judge` flag to engine
- Already planned, no additional design needed

### Complexity: Low (depends on #2)
### Risk: Low

---

## 4. Auth on API Server

**Why**: The server runs on 0.0.0.0:8080 with no auth. If exposed beyond localhost, anyone can use it.

**Approach**: Simple API key auth via Bearer token or `x-api-key` header. No OAuth, no JWT — keep it minimal.

### Changes
- `config.toml`: Add `server.api_key` field (optional, empty = no auth)
- `server.py`: Add FastAPI `Depends` middleware checking `Authorization: Bearer <key>` header
- Only apply when `server.api_key` is set (backward compatible)

### Complexity: Low
### Risk: Low — standard FastAPI pattern

---

## 5. Reasoning/Thinking Mode

**Why**: NVIDIA Nemotron supports a thinking/reasoning mode that lets the model do chain-of-thought before responding. Currently commented out in config.

**Approach**: Wire through the existing `reasoning_budget` and `enable_thinking` config fields. The client already has `extra_body` support for these — just need to:
1. Load them from `config.toml` (they're not loaded from features)
2. Pass them to the client properly
3. Expose in CLI and API

### Changes
- `config.py`: Load `reasoning_budget` and `enable_thinking` from `config.toml` under `[llm]` section
- `client.py`: Already has the code, verify it works with the NVIDIA API
- `cli.py`: Add `--reasoning-budget` and `--enable-thinking` flags
- `server.py`: Support `reasoning` params in request body

### Complexity: Low
### Risk: Medium — depends on NVIDIA API behavior, may need testing

---

## 6. Additional Tools

**Why**: Only `shell` exists. The design doc envisions `read_file`, `write_file`, `grep`, `glob`, `git`, `python`, `web_search`.

**Approach**: Add tools incrementally as needed. Each tool is a function + schema registration.

### Priority Tools
1. **`write_file`** — Write content to a file (safer than `echo "content" > file` via shell)
2. **`read_file`** — Read file contents (safer, no shell injection)
3. **`glob`** — Find files matching pattern
4. **`grep`** — Search file contents with regex

### Lower Priority
- `git` — Git operations (status, diff, commit)
- `python` — Run Python code in isolated environment
- `web_search` — DuckDuckGo search

### Complexity: Low per tool
### Risk: Low — each is independent

---

## Recommended Order

1. **Engine refactor** (`engine.py`) — unlocks #2 and #3 simultaneously
2. **Streaming** — complements engine refactor (progress reporting via SSE)
3. **Auth** — quick win, security improvement
4. **Reasoning mode** — config wiring, low effort
5. **Additional tools** — incremental, as needed

## Files Affected

| File | Changes |
|------|---------|
| `nano_harness/engine.py` | **New** — shared execution logic |
| `nano_harness/cli.py` | Slim down, delegate to engine |
| `nano_harness/server.py` | Wire planning/judge/streaming/auth |
| `nano_harness/client.py` | Add `chat_stream()` method |
| `nano_harness/config.py` | Load reasoning from toml |
| `nano_harness/tools.py` | Add new tool functions |
| `config.toml` | Add `[server]` section + reasoning settings |
