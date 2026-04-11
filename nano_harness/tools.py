"""Tool registry and execution for nano-harness."""
import subprocess
from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str
    error: str = ""


# Tool function signature
ToolFunc = Callable[[dict], ToolResult]


def shell_tool(params: dict) -> ToolResult:
    """Execute a shell command."""
    command = params.get("command", "")
    if not command:
        return ToolResult(success=False, output="", error="No command provided")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        return ToolResult(
            success=result.returncode == 0,
            output=output,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output="", error="Command timed out")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: dict[str, dict] = {}

    def register(self, name: str, func: ToolFunc, schema: dict) -> None:
        """Register a tool."""
        self._tools[name] = func
        self._schemas[name] = schema

    def get_schema(self, name: str) -> dict:
        """Get tool schema."""
        return self._schemas.get(name, {})

    def get_all_schemas(self) -> list[dict]:
        """Get all tool schemas in OpenAI format."""
        return list(self._schemas.values())

    def execute(self, name: str, params: dict) -> ToolResult:
        """Execute a tool by name."""
        if name not in self._tools:
            return ToolResult(success=False, output="", error=f"Unknown tool: {name}")
        return self._tools[name](params)

    def names(self) -> list[str]:
        """List all tool names."""
        return list(self._tools.keys())


# Default registry instance
_default_registry = ToolRegistry()

# Register shell tool
_default_registry.register(
    "shell",
    shell_tool,
    {
        "type": "function",
        "function": {
            "name": "shell",
            "description": "Execute a shell command and return the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    },
                },
                "required": ["command"],
            },
        },
    },
)


def get_registry() -> ToolRegistry:
    """Get the default tool registry."""
    return _default_registry