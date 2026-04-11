# Nano Harness

Minimal multi-agent framework for nano-class models (e.g., Nemotron-3-nano-30b-a3b).

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure LLM

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
# Edit .env with your NVIDIA API key
```

### 3. Run a Task

```bash
uv run python -m nano_harness.cli run "What is 2+2?"
```

## CLI Options

| Option | Alias | Description | Default |
|--------|-------|-------------|---------|
| `--system` | - | System prompt | (none) |
| `--temperature` | `-t` | Sampling temperature | 0.7 |
| `--max-rounds` | - | Max execution rounds | 5 |
| `--db` | - | Database path | nano_harness.db |

### Examples

```bash
# Simple task
uv run python -m nano_harness.cli run "List files in current directory"

# Custom system prompt
uv run python -m nano_harness.cli run "Write a hello world program" --system "You are a helpful coding assistant."

# Lower temperature for deterministic output
uv run python -m nano_harness.cli run "What is 5*5?" -t 0.2

# Enable checkpointing (enabled by default in config.toml)
uv run python -m nano_harness.cli run "Your task here" --max-rounds 3
```

## Features

Feature flags in `config.toml`:

```toml
[features]
candidate_judge = false    # External subagent evaluates candidate
multi_step_planning = false  # Decompose into multiple steps
subagents = false           # Specialized agents vs single orchestrator
checkpointing = true      # Persist state between rounds
```

## Architecture

```
nano_harness/
├── config.py    # Load .env + feature flags
├── client.py    # LLM API client (OpenAI-compatible)
├── tools.py    # Tool registry + shell execution
├── state.py     # SQLite checkpointing
└── cli.py       # CLI entry point
```

## Available Tools

- `shell` - Execute shell commands

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Lint
uv run ruff check nano_harness/

# Test connectivity
uv run python -c "
from nano_harness import load_config, LLMClient
c = load_config()
llm = LLMClient(c)
print(llm.chat([{'role': 'user', 'content': 'hi'}]).content)
"
```