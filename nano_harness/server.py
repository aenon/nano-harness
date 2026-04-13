"""OpenAI-compatible API server for nano-harness."""
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .client import LLMClient
from .config import load_config
from .tools import get_registry


app = FastAPI(title="nano-harness API")


# --- Request/Response Models ---

class Message(BaseModel):
    role: str
    content: str


class Tool(BaseModel):
    type: str = "function"
    function: dict


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[list[Tool]] = None
    stream: Optional[bool] = False


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: Usage


# --- Helpers ---

def convert_tools_for_harness(tools: Optional[list[Tool]]) -> Optional[list[dict]]:
    """Convert OpenAI tool format to our format."""
    if not tools:
        return None
    
    result = []
    for tool in tools:
        if tool.type == "function" and tool.function:
            result.append({
                "type": "function",
                "function": {
                    "name": tool.function.get("name"),
                    "description": tool.function.get("description", ""),
                    "parameters": tool.function.get("parameters", {}),
                }
            })
    return result


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    planning: bool = False,
    judge: bool = False,
    judge_criteria: str = "",
    max_rounds: int = 5,
):
    """Handle chat completion requests.
    
    Query params:
    - planning: Enable multi-step planning
    - judge: Enable candidate-judge self-verification
    - judge_criteria: Success criteria for judge
    - max_rounds: Max execution rounds (default 5)
    """
    # Load config
    config = load_config()
    
    # Override with request params
    if request.temperature is not None:
        config.temperature = request.temperature
    if request.max_tokens is not None:
        max_tokens = request.max_tokens
    else:
        max_tokens = 4096
    
    # Initialize
    llm = LLMClient(config)
    tools = get_registry()
    
    # Convert messages - filter out tool messages (we handle them differently)
    messages = []
    for msg in request.messages:
        if msg.role == "system":
            # Prepend to system prompt
            if config.system_prompt:
                config.system_prompt = f"{config.system_prompt}\n{msg.content}"
            else:
                config.system_prompt = msg.content
        elif msg.role == "tool":
            # Tool result - handled in loop below
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "tool_call_id": getattr(msg, "tool_call_id", None),
            })
        else:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
    
    # Convert tools
    tool_schemas = convert_tools_for_harness(request.tools)
    
    # Simple single-step execution (no planning/judge via API yet)
    # TODO: Add support for planning & judge modes
    response = llm.chat(messages, tools=tool_schemas, max_tokens=max_tokens)
    
    # Build response
    tool_calls = None
    if response.tool_calls:
        tool_calls = []
        for tc in response.tool_calls:
            tool_calls.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
            })
    
    # Estimate tokens (rough approximation)
    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages) * 1.3
    completion_tokens = len((response.content or "").split()) * 1.3
    
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
        created=int(time.time()),
        model=request.model,
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=tool_calls,
                ),
                finish_reason="tool_calls" if tool_calls else "stop",
            )
        ],
        usage=Usage(
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            total_tokens=int(prompt_tokens + completion_tokens),
        ),
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)