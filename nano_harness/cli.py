"""CLI entry point for nano-harness."""
import re

import click

from .client import LLMClient
from .config import load_config
from .state import get_state
from .tools import get_registry

PLANNING_PROMPT = """You are a task planner. Break down the user's task into actionable steps.
Format: Each step on a new line, starting with "- ". Keep steps simple and sequential."""


@click.group()
def cli():
    """Nano Harness - Multi-agent framework for nano-class models."""
    pass


@cli.command()
@click.argument("task")
@click.option("--system", default="", help="System prompt")
@click.option("--temperature", "-t", default=0.7, type=float, help="Sampling temperature")
@click.option("--max-rounds", default=5, help="Maximum execution rounds")
@click.option("--db", default="nano_harness.db", help="Database path")
def run(task: str, system: str, temperature: float, max_rounds: int, db: str):
    """Run a task with the LLM and tools."""
    config = load_config()

    # CLI options override config
    if system:
        config.system_prompt = system
    if temperature:
        config.temperature = temperature

    # Check required config
    if not config.llm_base_url or not config.llm_api_key:
        click.echo("Error: LLM not configured. Check .env file.")
        return

    # Initialize
    llm = LLMClient(config)
    tools = get_registry()
    state = get_state(db)

    click.echo(f"Running task: {task}")
    click.echo(f"Model: {config.llm_model}")
    click.echo(f"Features: candidate_judge={config.candidate_judge}, "
               f"multi_step={config.multi_step_planning}, "
               f"subagents={config.subagents}, "
               f"checkpointing={config.checkpointing}")
    click.echo("-" * 40)

    # Multi-step planning mode
    if config.multi_step_planning:
        _run_with_planning(llm, tools, state, config, task, max_rounds)
    else:
        _run_simple(llm, tools, state, config, task, max_rounds)


def _run_with_planning(llm, tools, state, config, task: str, max_rounds: int):
    """Run a task with multi-step planning."""
    # Phase 1: Planning
    click.echo("\n[Planning] Creating plan...")
    planning_messages = [
        {"role": "system", "content": PLANNING_PROMPT},
        {"role": "user", "content": f"Task: {task}\nBreak down into steps:"},
    ]
    response = llm.chat(planning_messages)
    plan_text = response.content

    # Parse steps from response
    steps = _parse_steps(plan_text)
    if not steps:
        click.echo("Failed to parse plan, running without planning.")
        _run_simple(llm, tools, state, config, task, max_rounds)
        return

    # Save steps to state
    state.save_plan_steps(task, steps)
    click.echo(f"[Planning] Done. {len(steps)} steps identified.")

    # Show plan
    for i, step in enumerate(steps, 1):
        click.echo(f"  {i}. {step}")

    # Phase 2: Execute each step
    for step_num, step_desc in enumerate(steps, 1):
        click.echo(f"\n[Step {step_num}/{len(steps)}] {step_desc}")

        # Execute step with retry
        success = _execute_step(llm, tools, state, config, task, step_num, step_desc, max_rounds)

        if success:
            click.echo(f"  [Step {step_num}] Complete.")
        else:
            click.echo(f"  [Step {step_num}] Failed after {config.planning_retry_limit} retries.")

    click.echo("\n" + "=" * 40)
    click.echo("Execution complete.")


def _execute_step(llm, tools, state, config, task: str, step_num: int, step_desc: str, max_rounds: int) -> bool:
    """Execute a single step with retry logic."""
    retry_limit = config.planning_retry_limit

    for attempt in range(1, retry_limit + 1):
        if attempt > 1:
            click.echo(f"  [Retry {attempt}/{retry_limit}]")

        messages = [{"role": "user", "content": step_desc}]
        step_failed = False

        for round_num in range(1, max_rounds + 1):
            tool_schemas = tools.get_all_schemas() if tools.names() else None
            response = llm.chat(messages, tools=tool_schemas)

            # Add to messages
            messages.append({"role": "assistant", "content": response.content})

            # Handle tool calls
            if response.tool_calls:
                for tc in response.tool_calls:
                    click.echo(f"  Tool: {tc.name}({tc.arguments})")
                    result = tools.execute(tc.name, tc.arguments)

                    output = result.output[:200] if result.output else result.error
                    click.echo(f"  Result: {output}{'...' if len(result.output or result.error) > 200 else ''}")

                    if not result.success:
                        step_failed = True
                        break

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result.output,
                    })

                if step_failed:
                    break
            else:
                # No tool calls - step complete
                break

        if not step_failed:
            # Success - save to state
            if config.checkpointing:
                state.update_step_status(step_num, "completed", result="Step completed successfully")
            return True

    # Failed after all retries
    if config.checkpointing:
        state.update_step_status(step_num, "failed", result="Failed after retries")
    return False


def _parse_steps(text: str) -> list[str]:
    """Parse steps from planning response."""
    # Look for lines starting with "- "
    steps = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            steps.append(line[2:])
        elif line.startswith("1. ") or line.startswith("2. "):
            # Also handle numbered lists
            match = re.match(r"^\d+\.\s+(.+)", line)
            if match:
                steps.append(match.group(1))
    return steps


def _run_simple(llm, tools, state, config, task: str, max_rounds: int):
    """Run a task without multi-step planning."""
    # Build messages
    messages = [{"role": "user", "content": task}]

    # Execution loop
    for round_num in range(1, max_rounds + 1):
        click.echo(f"\n[Round {round_num}]")

        # Get tool schemas
        tool_schemas = tools.get_all_schemas() if tools.names() else None

        # Call LLM
        response = llm.chat(messages, tools=tool_schemas)

        # Display response
        click.echo(f"LLM: {response.content[:500]}{'...' if len(response.content) > 500 else ''}")

        # Add assistant message
        messages.append({"role": "assistant", "content": response.content})

        # Save to state if checkpointing enabled
        if config.checkpointing:
            state.save_round(
                task=task,
                round_num=round_num,
                prompt=messages[-2]["content"],
                response=response.content,
                tool_calls=[{"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                            for tc in response.tool_calls],
            )

        # Handle tool calls
        if response.tool_calls:
            for tc in response.tool_calls:
                click.echo(f"Tool call: {tc.name}({tc.arguments})")

                # Execute tool
                result = tools.execute(tc.name, tc.arguments)

                # Display result
                output = result.output[:200] if result.output else result.error
                click.echo(f"Result: {output}{'...' if len(result.output or result.error) > 200 else ''}")

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result.output if result.success else result.error,
                })
        else:
            # No more tool calls, we're done
            break

    click.echo("\n" + "=" * 40)
    click.echo("Execution complete.")


@cli.command()
def history():
    """Show task execution history."""
    state = get_state()
    records = state.get_history("test", limit=10)

    for record in records:
        click.echo(f"Round {record.round}: {record.prompt[:50]}...")
        click.echo(f"  Response: {record.response[:100]}...")


@cli.command()
def clear():
    """Clear task history."""
    state = get_state()
    state.clear()
    click.echo("History cleared.")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()