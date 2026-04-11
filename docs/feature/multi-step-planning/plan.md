# Multi-Step Planning Design

## Goal

Decompose complex tasks into smaller steps before execution.

## Why

- Nano models have limited context window
- Breaking down helps reasoning
- Can track progress across steps

## Design Options

### Option A: Prompt Decomposition (Simpler)

1. **Step 1:** Send task to LLM with prompt asking for steps
2. Parse response into list of steps
3. Execute each step via tool calls
4. Aggregate results

```
User: "Create a hello world program in Python"

[LLM Planning] → "Step 1: Write file hello.py with 'print("Hello World")'"
[Execute] → Call shell tool
[Result] → Success
```

### Option B: Structured Output (More Complex)

Use tool with JSON schema to get structured steps:
```json
{
  "steps": [
    {"id": 1, "action": "write_file", "file": "hello.py", "content": "..."},
    {"id": 2, "action": "run", "command": "python hello.py"}
  ]
}
```

## Suggested: Option A (Prompt Decomposition)

### Implementation Sketch

1. In `cli.py` or new `planner.py`:
   - Detect `multi_step_planning = true` in config
   - Before main loop, call LLM with planning system prompt
   - Parse steps from response

2. Planning prompt (default):
   ```
   You are a task planner. Break down the user's task into a list of actionable steps.
   Format: Each step on a new line, starting with "- "
   ```

3. Store steps in state (optional)

4. Execute steps sequentially

## Key Questions

1. Should steps be executed one-by-one or all at once?
2. How to handle step failure? (stop vs continue)
3. Should user see the plan before execution?

## Alternatives Considered

- **candidates_judge:** Uses 2nd LLM to evaluate, more complex
- **subagents:** Multiple specialized agents, out of scope for now