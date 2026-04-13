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

## Decisions (All Made)

| # | Question | Decision |
|---|----------|----------|
| 1 | When to invoke | Every round |
| 2 | What to evaluate | Feedback + success criteria |
| 3 | Prompt structure | Fixed template |
| 4 | Feedback format | Natural language, prefixed |
| 5 | Retry logic | Max 2 retries |
| 6 | Cost | Accept 2x |
| 7 | Model | Same model |
| 8 | Blocking | Blocking |

## Judge Prompt Template

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

## Edge Cases

| Case | How to Handle |
|------|--------------|
| Partial success | Judge marks which criteria passed/failed |
| Criteria unclear | Use defaults (exit code 0, output non-empty) |
| Timeout | Judge marks as "needs investigation" |
| Infinite loop | Max 2 retries, then give up |

## Implementation Sketch

```python
def run_with_judge(task, criteria, max_rounds):
    for round in range(max_rounds):
        result = llm(task, history)
        tool = extract_tool(result)
        output = execute(tool)
        
        if config.judge_enabled:
            judgment = judge(task, criteria, output)
            if not judgment.success:
                task = f"{original_task}. Feedback: {judgment.fix}"
                continue
        break
```

## Next Steps

1. [x] Decide all 8 questions
2. [ ] Implement judge in config/harness
3. [ ] Add CLI flag `--judge`
4. [ ] Test with verification prompts