"""OpenAI 兼容 API 适配器（DeepSeek / GPT / 其他 OpenAI 格式提供方）。

仅处理文本回复；不做 tool call、streaming。
配置由 RuntimeSettings 注入，不自行读取环境变量。
"""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

import httpx

from my_claude_code.providers.adapter import ModelAdapter

if TYPE_CHECKING:
    from my_claude_code.config.settings import RuntimeSettings
    from my_claude_code.core.types import (
        ChatMessage,
        ProviderUsage,
        StepDiagnostics,
        ToolCall,
        ToolDefinition,
    )


def _to_chat_completion_messages(
    messages: list[ChatMessage], system_prompt: str = ""
) -> list[dict]:
    result: list[dict] = []
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
    for m in messages:
        if m.role.value == "user":
            result.append({"role": "user", "content": m.content})
        elif m.role.value == "assistant":
            result.append({"role": "assistant", "content": m.content})
    return result


def _should_retry(status: int) -> bool:
    return status in (429, 502, 503, 504)


def _calc_delay(retry_count: int, retry_after: str | None = None) -> float:
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    base = min(2**retry_count, 32)
    return base + random.uniform(0, 1)


def _parse_chat_completion(body: dict) -> tuple[str, list, ProviderUsage, StepDiagnostics]:
    from my_claude_code.core.types import ProviderUsage, StepDiagnostics

    choices = body.get("choices", [])
    text = ""
    stop_reason = ""
    if choices:
        msg = choices[0].get("message", {})
        text = msg.get("content") or ""
        stop_reason = choices[0].get("finish_reason", "")

    usage_data = body.get("usage", {})
    usage = ProviderUsage(
        input_tokens=usage_data.get("prompt_tokens", 0),
        output_tokens=usage_data.get("completion_tokens", 0),
    )

    diag = StepDiagnostics(stop_reason=stop_reason, usage=usage)
    return text, [], usage, diag


class OpenAICompatibleAdapter(ModelAdapter):
    """OpenAI /chat/completions 兼容适配器。"""

    MAX_RETRIES = 3

    def __init__(self, settings: RuntimeSettings, timeout: float = 120.0):
        self._api_key = settings.api_key
        self._base_url = settings.base_url.rstrip("/")
        self._model = settings.model
        self._timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model

    async def next(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        system_prompt: str = "",
        max_output_tokens: int = 4096,
        previous_step_diagnostics: StepDiagnostics | None = None,
    ) -> tuple[str, list[ToolCall], ProviderUsage, StepDiagnostics]:
        from my_claude_code.core.types import ProviderUsage, StepDiagnostics

        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY 未设置")

        api_messages = _to_chat_completion_messages(messages, system_prompt)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_error: str | None = None
        for retry in range(self.MAX_RETRIES + 1):
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": self._model,
                        "max_tokens": max_output_tokens,
                        "messages": api_messages,
                    },
                )

            if resp.is_success:
                return _parse_chat_completion(resp.json())

            if retry < self.MAX_RETRIES and _should_retry(resp.status_code):
                delay = _calc_delay(retry, resp.headers.get("retry-after"))
                await asyncio.sleep(delay)
                continue

            error_body = ""
            try:
                error_body = resp.text[:500]
            except Exception:
                pass
            last_error = f"HTTP {resp.status_code}: {error_body}"
            break

        return ("", [], ProviderUsage(), StepDiagnostics(error=last_error))
