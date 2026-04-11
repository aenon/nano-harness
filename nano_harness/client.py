"""LLM client for nano-harness."""
import json
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from .config import Config


@dataclass
class ToolCall:
    """Represents a tool call from the model."""
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    """LLM response with optional tool calls."""
    content: str
    tool_calls: list[ToolCall]
    reasoning: Optional[str] = None


class LLMClient:
    """Client for interacting with LLM via OpenAI-compatible API."""

    def __init__(self, config: Config):
        self.client = OpenAI(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
        )
        self.model = config.llm_model
        self.temperature = config.temperature
        self.system_prompt = config.system_prompt
        self.reasoning_budget = config.reasoning_budget
        self.enable_thinking = config.enable_thinking

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a chat request to the LLM."""
        # Build messages with system prompt if provided
        all_messages = []
        if self.system_prompt:
            all_messages.append({"role": "system", "content": self.system_prompt})
        all_messages.extend(messages)

        # Build extra body parameters
        extra_body = {}
        if self.reasoning_budget:
            extra_body["reasoning_budget"] = self.reasoning_budget
        if self.enable_thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": True}

        # Build request
        kwargs = {
            "model": self.model,
            "messages": all_messages,
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            kwargs["tools"] = tools
        if extra_body:
            kwargs["extra_body"] = extra_body

        response = self.client.chat.completions.create(**kwargs)

        # Extract content
        msg = response.choices[0].message
        content = msg.content or ""

        # Extract tool calls
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            reasoning=msg.reasoning,
        )