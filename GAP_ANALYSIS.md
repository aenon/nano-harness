# Gap Analysis - Nano Harness MVP

## 🔴 Resolved

| Gap | Decision |
|-----|----------|
| 1 | LLM: NVIDIA NIM endpoint, model nemotron-3-nano-30b-a3b |
| 2 | Tool: shell (bash command execution) |
| 3 | Success: Use larger model (GPT/Claude) to analyze results qualitatively |

## Current Status

- ✅ LLM configured (awaiting API key in .env)
- ✅ Tool: shell only
- ✅ Success criteria: Qualitative analysis by larger model
- ✅ Items 4-10: Decisions made above

| Gap | Description | Recommendation |
|-----|-------------|----------------|
| 4 | **Model behavior** - Will 30B do tool calling? | Test with simple reasoning prompt first |
| 5 | **Test prompt criteria** | Use qualitative (works/fails) for MVP, quantify later |
| 6 | **Checkpoint schema** | Keep minimal: task, round, prompt, response, tools |
| 7 | **Feature toggle** | If/else in code toggles behavior |

## 🟢 Minor (Can decide later)

| Gap | Description | Recommendation |
|-----|-------------|----------------|
| 8 | **CLI vs interactive** | Single prompt for MVP (simpler) |
| 9 | **Code execution** | Local subprocess (simpler than Docker) |
| 10 | **Parallel subagents** | Future phase |

### Decisions Made

| Item | Decision | Rationale |
|------|----------|------------|
| 4 | Test first | Verify model works before building |
| 5 | Two-tier: works/fails | Easy to evaluate |
| 6 | Minimal schema | Less friction, modify later |
| 7 | If/else toggles | Easier to implement |
| 8 | Single prompt | Simpler MVP |
| 9 | Local subprocess | No Docker setup needed |
| 10 | Not MVP | Future exploration |

---

## Assumptions & Risks

| Assumption | Risk Level | Note |
|-------------|------------|------|
| Model does tool calling | Medium | May need prompting tweaks |
| Local subprocess works | Low | Standard Python |
| Qualitative analysis works | Low | Proven method |

---

*Generated: 2026-04-10*