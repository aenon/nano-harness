# Multi-Step Planning Design

## Goal

Decompose complex tasks into smaller steps before execution.

## Why

- Nano models have limited context window
- Breaking down helps reasoning
- Can track progress across steps
- State stored externally (not in context, due to context limits)

## Design: Prompt Decomposition (Option A)

1. **Step 1:** Send task to LLM with planning prompt asking for steps
2. Parse response into list of steps
3. Execute each step sequentially
4. On failure: retry step (with limit), then continue
5. User sees plan as it's generated/updated/finished

```
User: "Create a hello world program in Python"

[LLM Planning] → "Step 1: Write file hello.py..."
[Execute step 1]
[LLM Review] → "Step 2: Run the file..."
[Execute step 2]
...
```

## Key Decisions (Final)

| Decision | Value |
|----------|-------|
| Execution | One-by-one (sequential) |
| State storage | External (SQLite DB, not context) |
| On failure | Retry step, then continue to next |
| Retry limit | TBD (suggest 2-3) |
| User visibility | See plan as generated/updated/finished |

## Implementation Sketch

### Config

In `config.toml`:
```toml
[features]
multi_step_planning = true
planning_retry_limit = 2  # optional
```

### Planning Prompt (default)

```
You are a task planner. Break down the user's task into actionable steps.
Format: Each step on a new line, starting with "- "
```

### State Schema (new table)

```sql
CREATE TABLE plan_steps (
    id INTEGER PRIMARY KEY,
    task TEXT NOT NULL,
    step_num INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, executing, completed, failed
    result TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Flow

1. **Planning phase:**
   - Call LLM with task + planning system prompt
   - Parse steps from response
   - Save to `plan_steps` table
   - User sees: "Planning... Done. N steps identified."

2. **Execution phase:**
   - For each step (in order):
     - Update status to "executing"
     - Execute via tools
     - On success: update to "completed"
     - On failure: increment retry, retry if < limit
   - User sees each step status update

3. **Review between steps:**
   - After step completes, optionally ask LLM for next step
   - Adapts plan based on results

## Key Questions Answered

- ✅ Steps executed one-by-one
- ✅ State stored externally (SQLite)
- ✅ On failure: retry, then continue
- ✅ User sees plan updates