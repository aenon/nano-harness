# Plan: CLI Options

Add CLI options for system prompt, temperature, and enable checkpointing feature.

## Changes

### config.py
- Add `system_prompt: str = ""` to Config dataclass
- Add `temperature: float = 0.7` to Config dataclass

### cli.py
- Add `--system` option (default: "")
- Add `--temperature` / `-t` option (default: 0.7)
- Pass to LLM client

### client.py
- Accept and use temperature parameter in chat()
- Use system prompt in messages[]

### config.toml
- Enable `checkpointing = true`

## Testing

- CLI help shows new options
- Run with custom system prompt
- Run with temperature 0.2
- Check history saved to DB