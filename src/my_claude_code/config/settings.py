"""运行时配置 — 多层配置 cascade 后的最终解析结果。

借鉴 MiniCode config.ts 的 RuntimeConfig + loadRuntimeConfig 模式：
  CLI 参数 > 环境变量 > settings.json provider 配置 > 默认值

每个 provider 的 env var、默认值都通过 _ProviderMeta 数据声明，添加新 provider
只需在 PROVIDERS 字典里加一条，不需要改任何逻辑代码。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from my_claude_code.config.paths import SETTINGS_FILE

# ── Provider 声明（数据驱动）─────────────────────────


@dataclass(frozen=True)
class _ProviderMeta:
    """单个 provider 的元数据：env var 命名规则 + 默认值。

    纯声明式数据，load_runtime_settings() 遍历解析，无 per-provider 分支。
    """

    key: str
    key_env: str  # API key 的主环境变量
    key_fallback_envs: tuple[str, ...] = ()  # API key 的 fallback 环境变量
    default_model: str = ""
    default_base_url: str = ""


# 所有支持的 provider 声明。加新 provider 只需在这里加一条。
PROVIDERS: dict[str, _ProviderMeta] = {
    "anthropic": _ProviderMeta(
        key="anthropic",
        key_env="ANTHROPIC_API_KEY",
        key_fallback_envs=("ANTHROPIC_AUTH_TOKEN",),
        default_model="claude-sonnet-4-6",
        default_base_url="https://api.anthropic.com",
    ),
    "deepseek": _ProviderMeta(
        key="deepseek",
        key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        default_base_url="https://api.deepseek.com/v1",
    ),
    "openai": _ProviderMeta(
        key="openai",
        key_env="OPENAI_API_KEY",
        default_model="gpt-4o",
        default_base_url="https://api.openai.com/v1",
    ),
}


# ── RuntimeSettings — 解析后的最终配置 ───────────────


@dataclass(frozen=True)
class RuntimeSettings:
    """解析后的运行时配置，所有字段已确定，可被 adapter 直接消费。"""

    provider: str
    model: str
    api_key: str
    base_url: str
    max_output_tokens: int = 4096
    providers: dict[str, dict[str, str]] = field(default_factory=dict)


# ── 配置加载 ────────────────────────────────────────


def _read_settings_file() -> dict[str, Any]:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid settings JSON: {SETTINGS_FILE}") from exc


def _get_env(*names: str) -> str:
    """返回第一个非空的环境变量值。"""
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _detect_provider() -> str | None:
    """自动检测：返回第一个在环境变量中已设置 API key 的 provider。"""
    for meta in PROVIDERS.values():
        if _get_env(meta.key_env, *meta.key_fallback_envs):
            return meta.key
    return None


def load_runtime_settings(
    provider: str | None = None,
    model: str | None = None,
) -> RuntimeSettings:
    """加载运行时配置，执行多层 cascade 后返回 RuntimeSettings。

    Provider 优先级：
    1. CLI --provider 参数
    2. MY_CLAUDE_PROVIDER 环境变量
    3. settings.json 的 "provider" 字段
    4. 自动检测（第一个有 API key 的 provider）
    5. 默认 anthropic

    每个字段的优先级：CLI > 专属环境变量 > settings.json provider段 > 默认值
    """
    settings = _read_settings_file()

    # ── 确定 provider ──
    selected = (
        provider
        or _get_env("MY_CLAUDE_PROVIDER")
        or str(settings.get("provider") or "")
        or _detect_provider()
        or "anthropic"
    ).lower()

    meta = PROVIDERS.get(selected)
    if meta is None:
        supported = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unsupported provider: {selected}. Supported: {supported}")

    # ── 获取 settings.json 中该 provider 的专属配置段 ──
    provider_section = settings.get("providers", {})
    if not isinstance(provider_section, dict):
        provider_section = {}
    pc = provider_section.get(selected, {})
    if not isinstance(pc, dict):
        pc = {}

    # ── 解析各字段（统一的 cascade 逻辑，不区分 provider）──
    resolved_model = (
        model
        or _get_env(f"{selected.upper()}_MODEL")
        or str(pc.get("model") or settings.get("model") or "")
        or meta.default_model
    )
    resolved_base_url = (
        _get_env(f"{selected.upper()}_BASE_URL")
        or str(pc.get("base_url") or settings.get("base_url") or "")
        or meta.default_base_url
    ).rstrip("/")
    resolved_api_key = (
        _get_env(meta.key_env, *meta.key_fallback_envs)
        or str(pc.get("api_key") or settings.get("api_key") or "")
    )

    # ── max_output_tokens ──
    resolved_max_tokens = 4096
    raw = _get_env("MY_CLAUDE_MAX_OUTPUT_TOKENS")
    if raw:
        try:
            resolved_max_tokens = max(1, int(raw))
        except ValueError:
            raise ValueError(f"Invalid MY_CLAUDE_MAX_OUTPUT_TOKENS: {raw}") from None

    # ── 收集所有 provider 配置（供后续扩展，如 /config 命令展示）──
    all_providers: dict[str, dict[str, str]] = {}
    for pk, pm in PROVIDERS.items():
        ppc = (provider_section.get(pk) if isinstance(provider_section, dict) else {}) or {}
        all_providers[pk] = {
            "model": str(ppc.get("model") or pm.default_model),
            "base_url": str(ppc.get("base_url") or pm.default_base_url),
        }

    return RuntimeSettings(
        provider=selected,
        model=resolved_model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        max_output_tokens=resolved_max_tokens,
        providers=all_providers,
    )
