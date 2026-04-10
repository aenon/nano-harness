# Nano Harness

> Exploring the limits of software development with small nano-class models (30B or 9B parameters).

## Overview

This project explores how a minimal multi-agent harness can enhance software development capabilities of small language models, specifically NVIDIA's Nemotron-3-nano-30b-a3b (and potentially other nano-class models).

## Motivation

Small models (9B-30B class) have inherent limitations:
- Limited reasoning depth for complex multi-step tasks
- Weaker self-verification capabilities
- Context sensitivity issues over long conversations

This harness compensates by:
- Delegating tasks to specialized subagents (same model class)
- Using candidate-judge patterns for critical evaluation
- Enabling long-running tasks with checkpointed state
- Combining external tools with internal reasoning

## Model

### Primary: Nemotron-3-nano-30b-a3b

| Specification | Value |
|---------------|-------|
| Parameters | 30B (MoE with activated experts) |
| Context Length | 128K |
| Architecture | Mixture-of-Experts (MoE) Hybrid Mamba-Transformer |

#### Benchmark Performance

| Benchmark | Score | Notes |
|-----------|-------|-------|
| AIME25 (no tools) | 89.1% | Math reasoning |
| SWE-Bench (OpenHands) | 38.8% | Software engineering |
| Terminal Bench (hard) | 8.5% | CLI tasks |
| LiveCodeBench | 68.3% | Code generation |
| GPQA | 73.0% | Graduate-level STEM |

> Note: Nemotron-3-nano-30b-a3b shows strong reasoning capability for its size class, making it a good candidate for agentic tasks.

## Architecture

### Core Pattern

```
                            Orchestrator (30B)
                    +---------------------------+
                    | - Task decomposition     |
                    | - Tool delegation      |
                    | - State management    |
                    | - Progress tracking |
                    +---------------------------+
                              |
        +---------------------+---------------------+---------------------+
        |                   |                     |                     |
        v                   v                     v                     v
+------------+    +------------+    +------------+    +------------+
| Research   |    | Review     |    | Execute    |    | External   |
| Agent      |    | Agent      |    | Agent      |    | Tools     |
|  (30B)    |    |  (30B)    |    |  (30B)    |    |           |
+------------+    +------------+    +------------+    +------------+
      |                 |                 |
      +-----------------+-----------------+
                              |
                    +---------------------------+
                    | External Tools            |
                    | (code, git, file, web)   |
                    +---------------------------+
```

### Agent Types

| Agent | Role | Tools |
|-------|------|-------|
| **Orchestrator** | Main coordinator, plans and delegates | Subagent invocation, tool dispatch |
| **Research Agent** | Finds information, explores codebase | Search, grep, documentation lookup |
| **Review Agent** | Evaluates candidates, catches errors | Code analysis, diff review |
| **Execute Agent** | Runs code, executes commands | Terminal, file operations |

### Patterns

#### 1. Candidate-Judge

- One subagent generates candidate solution
- Another subagent evaluates
- Loop until review passes or max iterations

```
Candidate Agent -> Review Agent -> (iterate until approved)
```

#### 2. Plan-and-Execute

- Planning agent creates step-by-step plan
- Execution agent implements each step
- Validation confirms completion

```
Planning Agent -> Execution Agent -> Validation
```

#### 3. Chained Reflection

- Bidirectional refinement loop
- Each iteration improves on previous

```
Agent A -> Agent B -> Agent A -> (refine)
```

## Expected Benefits vs Direct Tool Use

### What Direct Tool Use Provides

- Single model generates code/tool calls
- Results fed back to model
- Simple feedback loop

### What Nano Harness Adds

| Aspect | Direct Tool Use | Nano Harness |
|--------|---------------|-------------|
| **Self-verification** | Model judges itself | External subagent evaluates |
| **Planning** | Single-shot planning | Iterative decomposition |
| **Checkpointing** | None | Progress persistence |
| **Parallelism** | Sequential | Multiple subagents |
| **Specialization** | Generalist | Role-based agents |

### Potential Benefits

1. **Better error catching** - External evaluation may catch what self-reflection misses
2. **Parallel task handling** - Research can run in parallel with execution
3. **Longer task support** - Checkpointing enables hundreds of rounds
4. **Specialized reasoning** - Different subagents for different aspects

### Potential Costs

1. **Orchestration overhead** - More calls, more latency
2. **Coordination complexity** - State management
3. **Model capacity** - Each subagent uses full model calls

### Research Questions

- Does the harness meaningfully improve over direct model use?
- At what task complexity does the harness show benefit?
- Which pattern (candidate-judge, plan-execute, reflection) works best?
- How many rounds can this setup sustain?

---

## High-Level Design

### System Components

```
+------------------------------------------------------------+
|                      API Entry Point                         |
|                   (HTTP / WebSocket)                         |
+------------------------------------------------------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
+--------------+    +--------------+    +--------------+
|   Task       |    |   Agent     |    |  Checkpoint  |
|   Queue     |    |   Pool     |    |  Manager     |
|             |    |             |    |             |
| - pending   |    | - 30B nano |    | - state      |
| - running  |    |   agents   |    | - progress  |
| - done     |    | - tools    |    | - history   |
+--------------+    +--------------+    +--------------+
        |                   |                   |
        +-------------------+-------------------+
                            v
              +---------------------------+
              |      External Tools          |
              |  (code exec, git, file, web)  |
              +---------------------------+
```

### Component Details

#### 1. API Entry Point

| Endpoint | Method | Description |
|----------|--------|-------------|
| /task | POST | Submit new task |
| /task/{id} | GET | Get task status/result |
| /task/{id}/cancel | POST | Cancel running task |
| /agents | GET | List active agents |

#### 2. Task Queue

- FIFO queue for pending tasks
- Supports priority (optional)
- Tracks: task_id, status, created_at, started_at, completed_at

#### 3. Agent Pool

Manages 3+ specialized nano agents:

| Agent | System Prompt | Tools |
|-------|---------------|-------|
| orchestrator | You are the main coordinator. Break down tasks, delegate to specialized agents, and track progress. | invoke_subagent, execute_tool |
| research | You are a research agent. Find information, explore codebases, and gather context. | search, grep, read_file |
| review | You are a code review agent. Evaluate code quality, find bugs, and verify correctness. | diff, analyze, validate |
| execute | You are an execution agent. Run code, execute commands, and verify results. | bash, python, git |

#### 4. Checkpoint Manager

Persists state between rounds:

```python
@dataclass
class Checkpoint:
    task_id: str
    round: int
    state: dict           # Current state
    history: list        # Round history
    progress: float      # 0.0 - 1.0
    failed: bool
    error: str | None
```

#### 5. Tool Registry

External tools available to agents:

| Tool | Description |
|------|-------------|
| bash | Execute shell commands |
| python | Run Python code |
| read_file | Read file contents |
| write_file | Write to file |
| glob | Find files by pattern |
| grep | Search in files |
| git | Git operations |
| web_search | Search web |

### Workflow Execution Flow

#### Single Task Flow (Example: Fix a bug)

```
Round 0: Task submitted
  |
  v
+-- Orchestrator receives task --+
| "Fix the null pointer in     |
|  user.py line 42"            |
+-----------------------------+
  |
  v
+-- Decompose: 3 steps --------+
| 1. Read user.py line 40-45    |
| 2. Understand null cause    |
| 3. Apply fix                |
+-----------------------------+
  |
  +-> Research Agent: read file
  |     Returns: "line 42: user.name"
  |     -------------------------->
  |
  +-> Research Agent: search for user init
  |     Returns: "user = None"
  |     -------------------------->
  |
  +-> Review Agent: evaluate candidate
  |     "Null check needed: if user"
  |     -------------------------->
  |
  v
+-- Execute Agent: apply fix ----+
| "Changed to: if user and      |
|  user.name: ..."             |
+-----------------------------+
  |
  v
+-- Research: verify fix ------+
| Run tests -> pass             |
+-----------------------------+
  |
  v
Checkpoint saved -> Task complete
```

### Verification Design

The core research question: **Does the harness improve over direct model use?**

#### Baseline: Direct Model Use

```
Single model with tools (no harness)
+--------+    +--------+    +--------+
| Query  |--> |  Model |--> | Result |
|        |    | +tools |    |        |
+--------+    +--------+    +--------+

Flow:
1. Send task + tools to model
2. Model generates code/calls
3. Execute tool
4. Return result to model (feedback)
5. Repeat until done
```

#### Treatment: Harness Use

```
Model + harness (with subagents)
+--------+    +------------+    +--------+
| Query  |--> | Orchest.   |--> | Result |
|        |    | + subagents|    |        |
+--------+    +------------+    +--------+

Flow:
1. Send task to orchestrator
2. Orchestrator decomposes task
3. Delegate to Research/Review/Execute
4. Each subagent uses model
5. Checkpoint after each round
6. Repeat until complete
```

#### Metrics for Comparison

| Metric | Collection | Analysis |
|--------|-----------|----------|
| Success Rate | Task pass/fail | Compare % success |
| Time to Complete | Wall clock time | Compare median |
| Round Count | # model calls | Distribution |
| Error Rate | Failed rounds | Compare / category |
| Code Quality | Linting, tests | Compare scores |

#### Test Task Categories

| Category | Examples | Complexity |
|----------|----------|------------|
| Simple | Rename, format, single fix | Low |
| Medium | Multi-file changes, tests | Medium |
| Complex | Refactor, new feature | High |

#### Experiments

##### Experiment 1: Success Rate

```
Setup:
- Baseline: 50 simple + 50 medium + 50 complex tasks
- Treatment: Same tasks with harness

Compare: Pass rate per category
```

##### Experiment 2: Round Efficiency

```
Setup:
- Track # model calls per task
- Baseline: Direct tool loop
- Treatment: Orchestrator + subagents

Compare: Calls per task completion
```

##### Experiment 3: Error Analysis

```
Setup:
- Categorize errors (syntax, logic, tool, timeout)
- Track failure patterns

Compare: Error distribution
```

##### Experiment 4: Long-Running Tasks

```
Setup:
- Tasks requiring 50+ rounds
- Measure checkpoint recovery

Compare: Completion rate at round N
```

---

## Implementation Roadmap

### Tech Stack

```
Layer          | Option              | Notes
--------------|--------------------|-------------------
Web Framework | FastAPI            | Simple, async
Agent Logic   | Custom (minimal)   | Full control
Model API     | vLLM              | OpenAI-compatible
State        | SQLite + JSON files | Checkpoints
Task Queue   | asyncio.Queue      | In-process
```

### Phase 1: Minimal Viable Harness (Week 1-2)

- [ ] FastAPI server (basic endpoints)
- [ ] Task input/output handling
- [ ] Model client (vLLM API)
- [ ] Simple tool execution (subprocess)
- [ ] Checkpoint to file

### Phase 2: Multi-Agent Support (Week 3-4)

- [ ] Agent pool (orchestrator + subagents)
- [ ] Subagent invocation
- [ ] Tool dispatch
- [ ] State management (SQLite)

### Phase 3: Evaluation (Week 5-6)

- [ ] Benchmark suite
- [ ] Metrics collection
- [ ] Comparison baseline
- [ ] Analysis tools

### Phase 4: Optimization (Week 7-8)

- [ ] Pattern comparison
- [ ] Hyperparameter tuning
- [ ] Error analysis

---

## Future Exploration

- [ ] Switch between 30B and 9B models
- [ ] Compare harness vs direct use empirically
- [ ] Add more specialized agents
- [ ] Explore parallel execution
- [ ] Benchmark different patterns

---

## References

- [NVIDIA Nemotron-3-nano-30b-a3b](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b/modelcard)
- [Technical Report (PDF)](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Nano-Technical-Report.pdf)
- [Agentic Design Patterns](https://thenewstack.io/agentic-ai-design-patterns-in-2026/)

---

*Created: 2026-04-10*