"""模型适配器抽象接口。

所有真实模型适配器（Anthropic、DeepSeek、OpenAI-compatible 等）都实现此接口。
只暴露内部类型，不泄漏外部 API 细节。
"""

from abc import ABC, abstractmethod

from my_claude_code.core.types import (
    ChatMessage,
    ProviderUsage,
    StepDiagnostics,
    ToolCall,
    ToolDefinition,
)


class ModelAdapter(ABC):
    """模型适配器统一接口。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回此适配器的模型标识名。"""
        ...

    @abstractmethod
    async def next(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str = "",
        max_output_tokens: int = 4096,
        previous_step_diagnostics: StepDiagnostics | None = None,
    ) -> tuple[str, list[ToolCall], ProviderUsage, StepDiagnostics]:
        """发送消息，返回 (text, tool_calls, usage, diagnostics)。

        P1 只处理 text 返回；tool_calls 在后续里程碑中启用。
        """
        ...
