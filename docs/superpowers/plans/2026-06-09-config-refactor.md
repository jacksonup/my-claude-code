# 配置系统重构计划

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** 将模型配置从 adapter 内部移到统一的 config 层，实现 MiniCode 风格的 RuntimeConfig cascade，支持 settings.json 持久化多 provider 配置。

**Context:** 当前 env var 散落在各 adapter 的 `__init__` 中，`create_model()` 用字符串分支选择 provider，无法持久化配置。参考 MiniCode `config.ts` 的 `RuntimeConfig` + `loadRuntimeConfig()` 模式重构。

**Architecture:**
- `config/settings.py` — `RuntimeSettings` pydantic 模型 + `load_runtime_settings()` cascade
- CLI → `load_runtime_settings()` → `RuntimeSettings` → adapter `__init__(settings)` 
- Adapter 不再读 env var，只消费 `RuntimeSettings`

**Tech Stack:** pydantic v2

---

## Task 1: 定义 RuntimeSettings 模型

**Files:**
- Create: `src/my_claude_code/config/settings.py`

```python
"""运行时配置 — 多层配置 cascade 后的最终解析结果。

借鉴 MiniCode config.ts 的 RuntimeConfig + loadRuntimeConfig 模式：
  settings.json env 字段 → process.env → settings.json 直接字段 → CLI 参数
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


ProviderName = Literal["anthropic", "openai", "deepseek"]


class ProviderConfig(BaseModel):
    """单个 provider 的配置。"""

    model: str = ""
    base_url: str = ""
    api_key: str = ""


class RuntimeSettings(BaseModel):
    """解析后的运行时配置 — 所有值已确定，可直接消费。"""

    provider: ProviderName = "anthropic"
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    max_output_tokens: int = 4096

    # 所有已加载的 provider 配置（供 future use）
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


# ── 默认值 ──────────────────────────────────────────

DEFAULT_PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "anthropic": ProviderConfig(
        model="claude-sonnet-4-6",
        base_url="https://api.anthropic.com",
    ),
    "openai": ProviderConfig(
        model="gpt-4o",
        base_url="https://api.openai.com/v1",
    ),
    "deepseek": ProviderConfig(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
    ),
}

# Provider 对应的 API key 环境变量名
PROVIDER_KEY_ENV_VARS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}

# 兼容 fallback: 如果自己的 key env var 没设，尝试这些
PROVIDER_FALLBACK_KEY_ENV_VARS: dict[str, list[str]] = {
    "anthropic": ["ANTHROPIC_AUTH_TOKEN"],
    "openai": [],
    "deepseek": ["OPENAI_API_KEY"],
}


# ── 配置加载 ────────────────────────────────────────


def _settings_json_path() -> Path:
    home = os.environ.get("MY_CLAUDE_HOME", str(Path.home() / ".my-claude-code"))
    return Path(home) / "settings.json"


def _read_settings_file() -> dict:
    path = _settings_json_path()
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _resolve_api_key(provider: str) -> str:
    """解析 provider 对应的 API key。

    优先级：专属 env var > fallback env vars
    """
    primary = PROVIDER_KEY_ENV_VARS.get(provider, "")
    if primary:
        key = os.environ.get(primary, "")
        if key:
            return key

    for fallback in PROVIDER_FALLBACK_KEY_ENV_VARS.get(provider, []):
        key = os.environ.get(fallback, "")
        if key:
            return key

    return ""


def load_runtime_settings(
    provider: str | None = None,
    model: str | None = None,
) -> RuntimeSettings:
    """加载运行时配置，执行多层 cascade。

    优先级（从高到低）：
    1. CLI 参数 (provider, model)
    2. 对应 provider 的环境变量 (DEEPSEEK_API_KEY, OPENAI_API_KEY, etc.)
    3. settings.json 中的 providers 配置
    4. 默认值

    未指定 provider 时，检测环境变量自动选择。
    """
    file_settings = _read_settings_file()

    # 确定 provider：CLI > settings.json > 自动检测 > 默认
    if provider is None:
        provider = file_settings.get("provider")
    if provider is None:
        # 自动检测：根据哪个 provider 的 API key 已设置来决定
        for p in ["deepseek", "openai", "anthropic"]:
            if _resolve_api_key(p):
                provider = p
                break
    if provider is None:
        provider = "anthropic"

    # 获取该 provider 的默认配置
    defaults = DEFAULT_PROVIDER_CONFIGS.get(provider, ProviderConfig())

    # 从 settings.json 读取该 provider 的配置
    file_providers = file_settings.get("providers", {})
    file_provider_config = file_providers.get(provider, {})

    # 解析 model：CLI > env > settings.json > 默认
    resolved_model = model
    if resolved_model is None:
        model_env = os.environ.get(f"{provider.upper()}_MODEL", "")
        if model_env:
            resolved_model = model_env
    if resolved_model is None:
        resolved_model = file_providers.get(provider, {}).get("model", "")
    if not resolved_model:
        resolved_model = defaults.model

    # 解析 base_url：env > settings.json > 默认
    base_url_env = os.environ.get(f"{provider.upper()}_BASE_URL", "")
    resolved_base_url = base_url_env or file_provider_config.get("base_url", "") or defaults.base_url

    # 解析 api_key：env > settings.json
    resolved_api_key = _resolve_api_key(provider) or file_provider_config.get("api_key", "")

    # 解析 max_output_tokens
    resolved_max_tokens = int(os.environ.get("MY_CLAUDE_MAX_OUTPUT_TOKENS", "4096"))

    # 加载所有 provider 配置
    all_providers: dict[str, ProviderConfig] = {}
    for p_name, p_defaults in DEFAULT_PROVIDER_CONFIGS.items():
        fp = file_providers.get(p_name, {})
        all_providers[p_name] = ProviderConfig(
            model=fp.get("model", p_defaults.model),
            base_url=fp.get("base_url", p_defaults.base_url),
            api_key=fp.get("api_key", ""),
        )

    return RuntimeSettings(
        provider=provider,
        model=resolved_model,
        base_url=resolved_base_url,
        api_key=resolved_api_key,
        max_output_tokens=resolved_max_tokens,
        providers=all_providers,
    )
```

**Verify:**
```bash
python -c "from my_claude_code.config.settings import load_runtime_settings; s = load_runtime_settings(); print(s.model_dump())"
```

---

## Task 2: 写 settings.py 测试

**Files:**
- Create: `tests/test_settings.py`

```python
import os
from pathlib import Path

from my_claude_code.config.settings import load_runtime_settings


class TestLoadRuntimeSettingsDefaults:
    def test_defaults_to_anthropic(self):
        s = load_runtime_settings()
        assert s.provider == "anthropic"
        assert s.model == "claude-sonnet-4-6"
        assert s.base_url == "https://api.anthropic.com"

    def test_cli_provider_overrides(self):
        s = load_runtime_settings(provider="deepseek")
        assert s.provider == "deepseek"
        assert s.model == "deepseek-chat"

    def test_cli_model_overrides(self):
        s = load_runtime_settings(provider="deepseek", model="deepseek-reasoner")
        assert s.model == "deepseek-reasoner"

    def test_env_model_overrides_default(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v3")
        s = load_runtime_settings(provider="deepseek")
        assert s.model == "deepseek-v3"

    def test_cli_wins_over_env(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v3")
        s = load_runtime_settings(provider="deepseek", model="my-model")
        assert s.model == "my-model"

    def test_env_api_key_resolved(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test123")
        s = load_runtime_settings(provider="deepseek")
        assert s.api_key == "sk-test123"

    def test_env_base_url_resolved(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://custom.deepseek.com")
        s = load_runtime_settings(provider="deepseek")
        assert s.base_url == "https://custom.deepseek.com"

    def test_auto_detect_provider_by_key(self, monkeypatch):
        # Clear all provider keys, set only deepseek
        for env_var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]:
            monkeypatch.delenv(env_var, raising=False)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        s = load_runtime_settings()
        assert s.provider == "deepseek"
```

**Verify:**
```bash
pytest tests/test_settings.py -v
```

---

## Task 3: 重构 adapter 接收 RuntimeSettings

**Files:**
- Modify: `src/my_claude_code/providers/anthropic.py` — `__init__` 接收 `RuntimeSettings`
- Modify: `src/my_claude_code/providers/openai_compatible.py` — 同上

每个 adapter 改为：

```python
# anthropic.py
class AnthropicAdapter(ModelAdapter):
    def __init__(self, settings: RuntimeSettings, timeout: float = 60.0):
        self._api_key = settings.api_key
        self._base_url = settings.base_url.rstrip("/")
        self._model = settings.model
        self._timeout = timeout
```

不再读 `os.environ`。调用方负责传入已解析好的 `RuntimeSettings`。

---

## Task 4: 重构 runtime/app.py 的 create_model()

**Files:**
- Modify: `src/my_claude_code/runtime/app.py`

```python
def create_model(settings: RuntimeSettings) -> ModelAdapter:
    if not settings.api_key:
        raise RuntimeError(
            f"{settings.provider.upper()}_API_KEY 未设置"
        )

    if settings.provider == "anthropic":
        return AnthropicAdapter(settings)
    if settings.provider in ("openai", "deepseek"):
        return OpenAICompatibleAdapter(settings)

    raise ValueError(f"Unsupported provider: {settings.provider}")
```

CLI chat 命令改为：

```python
@main.command()
@click.option("--provider", default=None, help="anthropic | openai | deepseek")
@click.option("--model", default=None, help="模型名")
@click.option("--prompt", "-p", default="Hello")
def chat(provider: str | None, model: str | None, prompt: str):
    from my_claude_code.config.settings import load_runtime_settings
    from my_claude_code.runtime.app import create_model, run_chat

    settings = load_runtime_settings(provider=provider, model=model)
    click.echo(f"[provider: {settings.provider}, model: {settings.model}]")

    adapter = create_model(settings)
    text = asyncio.run(run_chat(adapter, prompt))
    click.echo(text)
```

同时添加 `config` 命令展示当前解析结果：

```python
@main.command()
@click.option("--provider", default=None)
def config(provider: str | None):
    """展示当前解析的运行时配置。"""
    from my_claude_code.config.settings import load_runtime_settings
    
    s = load_runtime_settings(provider=provider)
    click.echo(f"provider:  {s.provider}")
    click.echo(f"model:     {s.model}")
    click.echo(f"base_url:  {s.base_url}")
    click.echo(f"api_key:   {'***' + s.api_key[-4:] if s.api_key else '(not set)'}")
    click.echo(f"max_tokens:{s.max_output_tokens}")
```

---

## Task 5: 更新测试 + 全量验证

更新 `tests/test_runtime_app.py` 使用新的 `RuntimeSettings` 入参。

```bash
pytest tests/ -v        # 全量测试
ruff check src/ tests/  # lint
my-claude config                        # 展示默认配置
my-claude config --provider deepseek    # 展示 deepseek 配置
# 真实模型验证（需 API key）
DEEPSEEK_API_KEY=sk-xxx my-claude chat --provider deepseek --prompt "你好"
```

---

## 配置文件的 settings.json 格式

```json
{
  "provider": "deepseek",
  "providers": {
    "deepseek": {
      "model": "deepseek-chat",
      "base_url": "https://api.deepseek.com/v1",
      "api_key": "sk-xxx"
    },
    "anthropic": {
      "model": "claude-sonnet-4-6"
    }
  }
}
```

这样用户可以把 API key 存在 `~/.my-claude-code/settings.json` 里，不用每次都设环境变量。

---

## 改动清单

| 文件 | 操作 |
|------|------|
| `src/my_claude_code/config/settings.py` | 新建 — RuntimeSettings + load_runtime_settings |
| `tests/test_settings.py` | 新建 — cascade 测试 |
| `src/my_claude_code/providers/anthropic.py` | 修改 — __init__ 接收 RuntimeSettings |
| `src/my_claude_code/providers/openai_compatible.py` | 修改 — 同上 |
| `src/my_claude_code/runtime/app.py` | 修改 — create_model 接收 RuntimeSettings |
| `src/my_claude_code/cli.py` | 修改 — chat 用 load_runtime_settings，新增 config 命令 |
| `tests/test_runtime_app.py` | 修改 — 适配新签名 |

---

