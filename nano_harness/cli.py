"""CLI entry point for nano-harness."""
import click

from .client import LLMClient
from .config import load_config
from .state import get_state
from .tools import get_registry


@click.group()
def cli():
    """Nano Harness - Multi-agent framework for nano-class models."""
    pass


@cli.command()
@click.argument("task")
@click.option("--max-rounds", default=5, help="Maximum execution rounds")
@click.option("--db", default="nano_harness.db", help="Database path")
def run(task: str, max_rounds: int, db: str):
    """Run a task with the LLM and tools."""
    config = load_config()

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