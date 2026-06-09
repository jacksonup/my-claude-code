"""运行时 — 初始化模型适配器并运行一次对话。"""

from __future__ import annotations

from my_claude_code.config.settings import RuntimeSettings, load_runtime_settings
from my_claude_code.core.types import ChatMessage, MessageRole
from my_claude_code.providers.adapter import ModelAdapter
from my_claude_code.providers.anthropic import AnthropicAdapter
from my_claude_code.providers.openai_compatible import OpenAICompatibleAdapter

PROVIDER_ADAPTERS: dict[str, type[ModelAdapter]] = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAICompatibleAdapter,
    "deepseek": OpenAICompatibleAdapter,
}


def create_model(settings: RuntimeSettings) -> ModelAdapter:
    """根据 RuntimeSettings 创建模型适配器。"""
    if not settings.api_key:
        provider_upper = settings.provider.upper()
        raise RuntimeError(
            f"{provider_upper} API key 未设置："
            f"请配置 {provider_upper}_API_KEY 或 ~/.my-claude-code/settings.json"
        )

    adapter_cls = PROVIDER_ADAPTERS.get(settings.provider)
    if adapter_cls is None:
        raise ValueError(f"Unsupported provider: {settings.provider}")
    return adapter_cls(settings)


def load_settings(
    provider: str | None = None, model_name: str | None = None
) -> RuntimeSettings:
    """供 CLI 和诊断使用：加载并返回解析后的 RuntimeSettings。"""
    return load_runtime_settings(provider=provider, model=model_name)


async def run_chat(
    model: ModelAdapter,
    user_input: str,
    system_prompt: str = "",
    max_output_tokens: int = 4096,
) -> str:
    """发送单轮用户消息，返回模型回复文本。"""
    messages = [ChatMessage(role=MessageRole.USER, content=user_input)]
    text, _, _, diag = await model.next(
        messages=messages,
        tools=[],
        system_prompt=system_prompt,
        max_output_tokens=max_output_tokens,
    )
    if diag.error:
        return f"Error: {diag.error}"
    return text
