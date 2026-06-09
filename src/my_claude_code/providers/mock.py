"""Mock 模型 — 离线开发用，不消耗 API quota。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from my_claude_code.core.types import ProviderUsage, StepDiagnostics
from my_claude_code.providers.adapter import ModelAdapter

if TYPE_CHECKING:
    from my_claude_code.core.types import ChatMessage, ToolCall, ToolDefinition


class MockModel(ModelAdapter):
    """返回固定文本的 mock 模型。"""

    def __init__(
        self,
        text: str = "Mock response.",
        tool_calls: list[ToolCall] | None = None,
        model_name: str = "mock",
    ):
        self._text = text
        self._tool_calls = tool_calls or []
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def next(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str = "",
        max_output_tokens: int = 4096,
        previous_step_diagnostics: StepDiagnostics | None = None,
    ) -> tuple[str, list[ToolCall], ProviderUsage, StepDiagnostics]:
        return (
            self._text,
            list(self._tool_calls),
            ProviderUsage(input_tokens=0, output_tokens=0),
            StepDiagnostics(stop_reason="end_turn"),
        )
