# Candidate-Judge Feature Plan

## What is Candidate-Judge?

- Main agent produces a "candidate" (code, output, etc.)
- Judge agent evaluates: "Did the task succeed?"
- If failed, retry with feedback

## Why Not Currently Working

From our tests:
- Model retries blindly without understanding failure
- No verification of "Did step succeed?"
- No feedback provided to guide retry

## Gaps to Decided Together

## Decision: Judge Every Round ✅

**Chosen**: After each round - simpler flow, better feedback, fewer wasted retries.

### 1. When to Invoke Judge?

| Option | Pro | Con |
|--------|-----|-----|
| After each round | Early feedback | More LLM calls |
| After max rounds | Save calls | Blind retries |
| On explicit failure | Targeted | Requires detection |
| Every N steps | Balanced | Complexity |

**Question**: When should the judge run?

### 2. What Does Judge Evaluate?

| Option | Description |
|--------|------------|
| Binary | Success or fail only |
| Score | 1-10 quality score |
| Feedback | What's wrong and how to fix |
| All | All of above |

**Decision: Feedback with success criteria**

- Each task/step includes success criteria (e.g., "file exists", "output contains X")
- Judge evaluates: Does candidate meet success criteria?
- If not: What specifically is wrong and how to fix

### Edge Cases

| Case | How to Handle |
|------|--------------|
| Partial success | Judge marks which criteria passed/failed |
| Success criteria unclear | Use defaults (exit code 0, output non-empty) |
| Timeout/hang | Judge marks as "needs investigation" |
| Infinite loop | Max retries, then fail |

### 3. Judge Prompt Structure

**Decision: Fixed template, minimum instructions**

```
You are a judge. Evaluate if the candidate completed the task successfully.

Task: {task}
Success criteria: {criteria}
Candidate output: {output}

Respond in this format:
SUCCESS: true/false
REASON: (why it succeeded or failed)
FIX: (specific how to fix if failed)
```

**Why this works:**

| Element | Purpose |
|---------|---------|
| Fixed template | No per-task prompt engineering |
| SUCCESS: true/false | Machine-parseable |
| REASON | Human-readable explanation |
| FIX | Actionable retry guidance |

**Works for any candidate type:** code, error, text, empty, etc.

### 4. Feedback Format

**Decision: Natural language, prefixed format**

```
SUCCESS: true/false
REASON: (brief explanation)
FIX: (actionable step - "what to try next")
```

Examples:
- "Port 8000 in use, try 8080 instead"
- "File already exists, delete or use existing directory"
- "Syntax error on line 3, fix the parentheses"

Uses natural language but maintains 3-line structure.

### 5. Retry Logic

**Decision: Max 2 judge retries, then give up**

```
Round 1: LLM → Tool → Output → Judge → FAIL, FIX=...
Round 2: LLM + FIX → Tool → Output → Judge → FAIL, FIX=...
Round 3: Give up (fail the task)
```

- Judge says SUCCESS → Stop, return result
- Judge says FAIL → Add FIX to prompt, retry
- After 2 failures → Give up, return best effort

**Why 2?** Enough to fix simple issues, not enough to loop forever.

### 6. Cost Concern

**Decision: Accept 2x cost, trade for better verification**

- Judge adds 1 extra LLM call per round
- But likely fewer total rounds (no blind retries)
- Net: May not double cost, but simpler debugging

### 7. Model for Judge

**Decision: Same model, configurable**

- Use same model for consistency
- But make configurable in config.toml

**Decision: Same model, configurable**

- Use same model for consistency
- But make configurable in config.toml

### 8. Blocking vs Non-Blocking

**Decision: Blocking (simpler)**

- Wait for judge before continuing each round
- Simpler debugging: output → judge → next

---

## Implementation Sketch

```python
# Current flow (no judge)
def run(task, max_rounds):
    for round in range(max_rounds):
        result = llm(task, history)
        tool = extract_tool(result)
        output = execute(tool)
        history.add(output)

# With judge
def run_with_judge(task, max_rounds):
    for round in range(max_rounds):
        result = llm(task, history)
        tool = extract_tool(result)
        output = execute(tool)
        
        if config.judge_enabled:
            judgment = judge(task, output)
            if not judgment.success:
                feedback = judgment.feedback
                task = f"{original_task}. Feedback: {feedback}"
                continue
        break
```

---

## Next Steps

1. [ ] Decide all 8 questions above
2. [ ] Write judge_prompt.md with instructions
3. [ ] Implement judge in config.py/harness
4. [ ] Add CLI flag --judge
5. [ ] Test with verification prompts

---

## Questions for Discussion (Decided)

- [x] 1. When to invoke judge? → After each round
- [ ] 2. What does judge evaluate?
- [ ] 3. Judge prompt structure?
- [ ] 4. Feedback format?
- [ ] 5. Retry logic?
- [ ] 6. Accept 2x cost?
- [ ] 7. Model for judge?
- [ ] 8. Blocking or async?

---

## Implementation Checklist

When ready to implement:

- [ ] Write `docs/candidate-judge/judge_prompt.md`
  - [ ] Base instructions
  - [ ] Few-shot examples
  - [ ] Output format
  
- [ ] Implement judge in harness
  - [ ] `nano_harness/judge.py` - judge function
  - [ ] Update `config.py` - add judge config
  - [ ] Update `cli.py` - add `--judge` flag
  
- [ ] Test with verification prompts
  - [ ] Fibonacci venv test
  - [ ] API server test
  - [ ] Introspection test
  
- [ ] Verify improvement
  - [ ] Compare rounds needed (before vs after)
  - [ ] Compare success rate

---

### 9. Decision Priority

After discussing each question, we should implement in order of impact:

1. **Q2 (What to evaluate)** - Core to judge function
2. **Q5 (Retry logic)** - Prevents infinite loops
3. **Q4 (Feedback format)** - Makes retries actionable
4. **Q3 (Prompt structure)** - Drives evaluation quality
5. **Q1 (When to invoke)** - Already decided
6. **Q6 (Cost)** - Acceptable tradeoff
7. **Q7 (Model)** - Can tune later
8. **Q8 (Blocking)** - Can optimize later

---

## Questions for Discussion

Please review and let's decide together:
1. [x] When to invoke judge? ✅ (After each round)
2. [x] What does judge evaluate? ✅ (Feedback with success criteria)
3. [x] Judge prompt structure? ✅ (Fixed template)
4. [x] Feedback format? ✅ (Natural language, prefixed)
5. [x] Retry logic? ✅ (Max 2 retries)
6. [x] Accept 2x cost? ✅ (Accept trade-off)
7. [x] Model for judge? ✅ (Same model)
8. [x] Blocking or async? ✅ (Blocking)

### 5. Retry Logic

**Decision: Max 2 judge retries, then give up**

```
Round 1: LLM → Tool → Output → Judge → FAIL, FIX=...
Round 2: LLM + FIX → Tool → Output → Judge → FAIL, FIX=...
Round 3: Give up (fail the task)
```

- Judge says SUCCESS → Stop, return result
- Judge says FAIL → Add FIX to prompt, retry
- After 2 failures → Give up, return best effort

**Why 2?** Enough to fix simple issues, not enough to loop forever.

---

### 6. Cost Concern
7. [ ] Model for judge?
8. [ ] Blocking or async?
9. [x] Edge cases? ✅ (Added)