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


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from .env and config.toml."""
    # Load .env
    load_dotenv()

    # LLM config from env
    # Model ID format: "nvidia/nemotron-3-nano-30b-a3b" (use full path for NVIDIA NIM)
    model = os.getenv("LLM_MODEL", "nvidia/nemotron-3-nano-30b-a3b")
    # If model doesn't start with a namespace, add "nvidia/" prefix
    if "/" not in model:
        model = f"nvidia/{model}"

    config = Config(
        llm_base_url=os.getenv("LLM_BASE_URL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=model,
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
        system_prompt=os.getenv("SYSTEM_PROMPT", ""),
        reasoning_budget=int(os.getenv("REASONING_BUDGET", "0")) or None,
        enable_thinking=os.getenv("ENABLE_THINKING", "false").lower() == "true",
    )

    # Load features from config.toml if exists
    if config_path is None:
        config_path = os.getenv("NANO_CONFIG", "config.toml")

    config_file = Path(config_path)
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