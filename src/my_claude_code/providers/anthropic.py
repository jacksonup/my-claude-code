"""Anthropic Messages API 适配器。

仅处理文本回复；不做 tool call、streaming、thinking block（后续里程碑补齐）。
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import TYPE_CHECKING

import httpx

from my_claude_code.providers.adapter import ModelAdapter

if TYPE_CHECKING:
    from my_claude_code.core.types import (
        ChatMessage,
        ProviderUsage,
        StepDiagnostics,
        ToolCall,
        ToolDefinition,
    )


# ── 消息转换 ────────────────────────────────────────


def _to_api_messages(messages: list[ChatMessage]) -> list[dict]:
    """将内部消息列表转为 Anthropic Messages API 格式。

    system 消息不在此处理 —— 由顶层 system 参数传入。
    """
    api_msgs = []
    for m in messages:
        if m.role.value == "user":
            api_msgs.append({"role": "user", "content": m.content})
        elif m.role.value == "assistant":
            api_msgs.append({"role": "assistant", "content": m.content})
    return api_msgs


# ── retry 逻辑 ──────────────────────────────────────


def _should_retry(status: int) -> bool:
    return status in (429, 502, 503, 504)


def _calc_delay(retry_count: int, retry_after: str | None = None) -> float:
    """计算重试延迟：优先 retry-after header，否则指数退避 + jitter。"""
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    base = min(2**retry_count, 32)
    return base + random.uniform(0, 1)


# ── 响应解析 ────────────────────────────────────────


def _parse_response(body: dict) -> tuple[str, list, ProviderUsage, StepDiagnostics]:
    from my_claude_code.core.types import ProviderUsage, StepDiagnostics

    text_parts = []
    for block in body.get("content", []):
        if block["type"] == "text":
            text_parts.append(block["text"])

    usage_data = body.get("usage", {})
    usage = ProviderUsage(
        input_tokens=usage_data.get("input_tokens", 0),
        output_tokens=usage_data.get("output_tokens", 0),
        cache_read_tokens=usage_data.get("cache_read_input_tokens", 0),
        cache_write_tokens=usage_data.get("cache_creation_input_tokens", 0),
    )

    diag = StepDiagnostics(
        stop_reason=body.get("stop_reason", ""),
        usage=usage,
    )

    return "".join(text_parts), [], usage, diag


# ── 适配器 ──────────────────────────────────────────


class AnthropicAdapter(ModelAdapter):
    """Anthropic Messages API 适配器。"""

    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_MODEL = "claude-sonnet-4-6"
    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._base_url = (
            base_url or os.environ.get("ANTHROPIC_BASE_URL") or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._model = model or os.environ.get("ANTHROPIC_MODEL") or self.DEFAULT_MODEL
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
            raise RuntimeError("ANTHROPIC_API_KEY 未设置")

        api_messages = _to_api_messages(messages)
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        last_error: str | None = None
        for retry in range(self.MAX_RETRIES + 1):
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/v1/messages",
                    headers=headers,
                    json={
                        "model": self._model,
                        "max_tokens": max_output_tokens,
                        "system": system_prompt,
                        "messages": api_messages,
                    },
                )

            if resp.is_success:
                return _parse_response(resp.json())

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

        return (
            "",
            [],
            ProviderUsage(),
            StepDiagnostics(error=last_error),
        )
