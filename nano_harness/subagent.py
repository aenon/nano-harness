"""Subagent module — spawn specialized agents by running a mini nano-harness loop."""
import click
from typing import Optional

from .client import LLMClient
from .config import Config
from .tools import ToolRegistry, get_registry

# Default agent roles and their system prompts
AGENT_ROLES = {
    "research": (
        "You are a research agent. Your job is to find information, explore the codebase, "
        "and gather context. Use shell commands to read files, search, and investigate. "
        "Be thorough and return all relevant findings."
    ),
    "review": (
        "You are a code review agent. Evaluate code quality, find bugs, verify correctness, "
        "and check for edge cases. Use shell commands to inspect files and run tests. "
        "Be strict and return specific feedback with line references."
    ),
    "execute": (
        "You are an execution agent. Run code, execute commands, build, test, and verify results. "
        "Focus on getting things done and reporting clear outcomes. "
        "Always verify that commands succeeded."
    ),
}


class SubagentResult:
    """Result from a subagent run."""

    def __init__(self, output: str, tool_calls: list[dict]):
        self.output = output
        self.tool_calls = tool_calls


class Subagent:
    """A specialized agent that runs its own LLM+tool loop.

    Each subagent gets its own system prompt and can access a subset of tools.
    The orchestrator invokes subagents by calling .run(task).
    """

    def __init__(
        self,
        name: str,
        config: Config,
        tools: Optional[ToolRegistry] = None,
        max_rounds: int = 5,
        system_prompt: Optional[str] = None,
    ):
        self.name = name
        self.config = config
        self.tools = tools or get_registry()
        self.max_rounds = max_rounds
        # Use custom system prompt if given, otherwise look up default role
        self.system_prompt = system_prompt or AGENT_ROLES.get(name, "")
        self._llm = LLMClient(config)
        # Override the LLM's system prompt for this agent
        self._llm.system_prompt = self.system_prompt

    def run(self, task: str, verbose: bool = False) -> SubagentResult:
        """Run the subagent on a task. Returns accumulated output."""
        messages = [{"role": "user", "content": task}]
        all_tool_calls = []

        if verbose:
            click.echo(f"\n  [{self.name}] Subagent started: {task[:80]}...")

        for round_num in range(1, self.max_rounds + 1):
            tool_schemas = self.tools.get_all_schemas() if self.tools.names() else None
            response = self._llm.chat(messages, tools=tool_schemas)

            messages.append({"role": "assistant", "content": response.content})

            if verbose:
                click.echo(f"  [{self.name}] Round {round_num}: {response.content[:200]}")

            if response.tool_calls:
                for tc in response.tool_calls:
                    if verbose:
                        click.echo(f"  [{self.name}] Tool: {tc.name}({tc.arguments})")

                    result = self.tools.execute(tc.name, tc.arguments)
                    all_tool_calls.append({
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                    })

                    tool_output = result.output if result.success else f"ERROR: {result.error}"
                    if verbose:
                        click.echo(f"  [{self.name}] Result: {tool_output[:200]}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output,
                    })
            else:
                # No tool calls — final response
                if verbose:
                    click.echo(f"  [{self.name}] Done.")
                break

        # Build final output from tool results and last response
        output_parts = []
        if all_tool_calls:
            for tc_result in all_tool_calls:
                if tc_result["success"]:
                    output_parts.append(f"[{tc_result['name']}({tc_result['arguments']})]: {tc_result['output']}")
                else:
                    output_parts.append(f"[{tc_result['name']}({tc_result['arguments']})]: ERROR: {tc_result['error']}")

        # Add the final text response
        final_content = messages[-1].get("content", "") if messages else ""
        if final_content:
            output_parts.append(final_content)

        combined_output = "\n---\n".join(output_parts) if output_parts else final_content

        return SubagentResult(output=combined_output, tool_calls=all_tool_calls)


class AgentPool:
    """Manages a set of named subagents."""

    def __init__(self, config: Config, max_rounds: int = 5):
        self.config = config
        self.max_rounds = max_rounds
        self._agents: dict[str, Subagent] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default agent roles."""
        tools = get_registry()
        for name, prompt in AGENT_ROLES.items():
            self._agents[name] = Subagent(
                name=name,
                config=self.config,
                tools=tools,
                max_rounds=self.max_rounds,
                system_prompt=prompt,
            )

    def get(self, name: str) -> Optional[Subagent]:
        """Get a subagent by name."""
        return self._agents.get(name)

    def list(self) -> list[str]:
        """List available agent names."""
        return list(self._agents.keys())

    def create(
        self,
        name: str,
        system_prompt: str,
        max_rounds: Optional[int] = None,
    ) -> Subagent:
        """Create and register a custom subagent."""
        agent = Subagent(
            name=name,
            config=self.config,
            max_rounds=max_rounds or self.max_rounds,
            system_prompt=system_prompt,
        )
        self._agents[name] = agent
        return agent
