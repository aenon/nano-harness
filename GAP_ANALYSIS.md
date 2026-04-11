# Gap Analysis - Nano Harness MVP

## 🔴 Blocking (Must resolve before implementation)

| Gap | Description |
|-----|-------------|
| 1 | **LLM endpoint not available** - We have .env.example but no actual endpoint to test |
| 2 | **Tool definitions not specified** - What tools should be enabled? Which ones? |
| 3 | **Success criteria undefined** - How do we measure "good enough"? |

## 🟡 Important (Should resolve before code)

| Gap | Description |
|-----|-------------|
| 4 | **Model behavior expectation** - Will 30B model even do tool calling reliably? |
| 5 | **Test prompt success criteria** - What's expected vs actual? |
| 6 | **Checkpoint schema** - What data to persist? (state, history, progress?) |
| 7 | **Feature toggle behavior** - How does each flag change behavior? |

## 🟢 Minor (Can decide later)

| Gap | Description |
|-----|-------------|
| 8 | **CLI vs interactive mode** - Single prompt or multi-turn chat? |
| 9 | **Where to run code** - Local subprocess or Docker? |
| 10 | **Parallel subagents** - For future, not MVP |

---

## Questions to Answer

### For 🔴 Blocking:

1. **Do you have an LLM endpoint ready?** (vLLM or similar, OpenAI-compatible)
   - If not, we can't test anything

2. **What tools should the MVP support?**
   - Minimal: bash, read_file, write_file, grep?
   - Or expand later?

3. **What's the success target?**
   - e.g., "3/4 test prompts succeed with features OFF"
   - e.g., "Features ON improves by 20%"

### For 🟡 Important:

4. **Assuming Nemotron-3-nano-30b-a3b does tool calling** - should we verify with a simple test first?

5. **Checkpoint data model:**
   ```
   task_id, round, prompt, response, tools_used, timestamp
   ```
   - Or add more fields?

6. **Feature toggle implementation:**
   - candidate_judge = true → call ReviewAgent after each response
   - multi_step_planning = true → decompose into steps first
   - Is that correct?

---

## Current Assumptions (may be wrong)

| Assumption | Risk |
|------------|------|
| Model does tool calling out of box | 🔴 - Need verification |
| SQLite is sufficient for state | 🟢 - Probably fine |
| CLI is right interface | 🟢 - Can change later |

---

*Generated: 2026-04-10*