"""Configuration loader for nano-harness."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Nano Harness configuration."""

    # LLM
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # Sampling
    temperature: float = 0.7
    system_prompt: str = ""

    # Reasoning (optional)
    reasoning_budget: Optional[int] = None
    enable_thinking: bool = False

    # Features (default all off)
    candidate_judge: bool = False
    multi_step_planning: bool = False
    subagents: bool = False
    checkpointing: bool = False
    planning_retry_limit: int = 2


# Default system prompt for all LLM interactions
DEFAULT_SYSTEM_PROMPT = """You are a coding assistant. Execute the user's task using the available tools.

IMPORTANT VERIFICATION REQUIREMENTS:
1. After executing commands that modify state (file creation, installation, etc.), ALWAYS verify the result
2. Commands that succeed with empty output (e.g., `source venv`, `> file`) should be followed by a verification command
3. Verify with commands that produce visible output: `ls -la`, `cat file`, `echo $VAR`, `python -c "import module"`
4. Do not assume commands succeeded - always confirm with a verification step"""

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from .env and config.toml."""
    # Load .env
    load_dotenv()

    # Determine config file path
    if config_path is None:
        config_path = os.getenv("NANO_CONFIG", "config.toml")

    config_file = Path(config_path)
    llm_config = {}
    if config_file.exists():
        try:
            import tomllib

            with open(config_file, "rb") as f:
                data = tomllib.load(f)
            if "llm" in data:
                llm_config = data["llm"]
        except ImportError:
            # Python < 3.11, try tomli
            try:
                import tomli as tomllib

                with open(config_file, "rb") as f:
                    data = tomllib.load(f)
                if "llm" in data:
                    llm_config = data["llm"]
            except ImportError:
                pass  # No toml parser

    # Model from config or env (config takes precedence)
    model = llm_config.get("model") or os.getenv("LLM_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
    # If model doesn't start with a namespace, add "nvidia/" prefix
    if "/" not in model:
        model = f"nvidia/{model}"

    # Base URL from config or env (config takes precedence)
    base_url = llm_config.get("base_url") or os.getenv("LLM_BASE_URL", "")

    # API key - only from env var (do not store in config files)
    api_key = os.getenv("LLM_API_KEY", "")

    config = Config(
        llm_base_url=base_url,
        llm_api_key=api_key,
        llm_model=model,
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
        system_prompt=os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
        reasoning_budget=int(os.getenv("REASONING_BUDGET", "0")) or None,
        enable_thinking=os.getenv("ENABLE_THINKING", "false").lower() == "true",
    )

    # Load features from config.toml if exists
    if config_file.exists():
        try:
            import tomllib

            with open(config_file, "rb") as f:
                data = tomllib.load(f)
            if "features" in data:
                feats = data["features"]
                config.candidate_judge = feats.get("candidate_judge", False)
                config.multi_step_planning = feats.get("multi_step_planning", False)
                config.subagents = feats.get("subagents", False)
                config.checkpointing = feats.get("checkpointing", False)
                config.planning_retry_limit = feats.get("planning_retry_limit", 2)
        except ImportError:
            # Python < 3.11, try tomli
            try:
                import tomli as tomllib

                with open(config_file, "rb") as f:
                    data = tomllib.load(f)
                if "features" in data:
                    feats = data["features"]
                    config.candidate_judge = feats.get("candidate_judge", False)
                    config.multi_step_planning = feats.get("multi_step_planning", False)
                    config.subagents = feats.get("subagents", False)
                    config.checkpointing = feats.get("checkpointing", False)
            except ImportError:
                pass  # No toml parser, skip features

    return config