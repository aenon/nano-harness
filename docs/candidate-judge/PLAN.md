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
| All of above | Most comprehensive |

**Question**: What level of evaluation needed?

### 3. Judge Prompt Structure

```
You are a judge. Task: {task}
Candidate: {output}
Did it succeed? If not, why and how to fix?
```

**Question**: What instructions and few-shot examples?

### 4. Feedback Format

| Format | Example |
|--------|--------|
| Natural language | "Server not running on port 8000" |
| JSON | `{"issue": "...", "fix": "..."}` |
| Structured | ISSUE=..., FIX=... |

**Question**: What format is most actionable?

### 5. Retry Logic

- Max judge retries: 1? 2? 3?
- When to give up: After X failures?
- Escalation: What if judge keeps failing?

**Question**: How many retries before giving up?

### 6. Cost Concern

- 2 LLM calls per round → 2x cost
- Is it worth it? 
- When does it help most?

**Question**: Accept 2x cost for better verification?

### 7. Model for Judge

Options:
- Same model (consistent)
- Smaller model (faster, cheaper)
- Configurable

**Question**: Same or different model?

### 8. Blocking vs Non-Blocking

- Blocking: Wait for judge before continuing
- Async: Run judge in parallel, check later

**Question**: Should we block execution?

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

## Questions for Discussion

Please review and let's decide together:
1. [x] When to invoke judge? ✅ (After each round)
2. [ ] What does judge evaluate?
3. [ ] Judge prompt structure?
4. [ ] Feedback format?
5. [ ] Retry logic?
6. [ ] Accept 2x cost?
7. [ ] Model for judge?
8. [ ] Blocking or async?