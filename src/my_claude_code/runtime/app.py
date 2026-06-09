"""运行时 — 初始化模型适配器并运行一次对话。"""

from __future__ import annotations

from my_claude_code.core.types import ChatMessage, MessageRole
from my_claude_code.providers.adapter import ModelAdapter
from my_claude_code.providers.anthropic import AnthropicAdapter
from my_claude_code.providers.mock import MockModel


def create_model(model_name: str | None = None) -> ModelAdapter:
    """根据 model_name 创建对应的适配器。"""
    if model_name == "mock":
        return MockModel()
    return AnthropicAdapter(model=model_name)


async def run_chat(
    model: ModelAdapter,
    user_input: str,
    system_prompt: str = "",
) -> str:
    """发送单轮用户消息，返回模型回复文本。"""
    messages = [ChatMessage(role=MessageRole.USER, content=user_input)]
    text, _, _, diag = await model.next(
        messages=messages,
        tools=[],
        system_prompt=system_prompt,
    )
    if diag.error:
        return f"Error: {diag.error}"
    return text
