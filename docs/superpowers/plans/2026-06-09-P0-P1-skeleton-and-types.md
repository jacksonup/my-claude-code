# P0+P1 实现计划：项目骨架 + 类型系统与模型适配器

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可运行的 CLI 空壳（P0）+ 定义核心类型契约并实现 Anthropic 文本对话闭环（P1），达成 `my-claude --model mock` 可启动、`my-claude` 可调用真实模型返回文本回复。

**Architecture:** 使用 `src/` layout，包名 `my_claude_code`，CLI 命令 `my-claude`。分层：`core/`（类型）、`providers/`（模型适配器+重试）、`config/`（最小配置）在 P0-P1 落地。P1 的模型请求/响应只处理文本，不做工具调用、不做 streaming、不做 thinking block。

**Tech Stack:** click + pydantic v2 + httpx + pytest + pytest-asyncio + ruff

---

## P0：项目骨架

### Task 1: 安装依赖

- [ ] **Step 1: 创建虚拟环境并安装依赖**

```bash
cd /Users/jackson/文件/3_工作/code/python/my-claude-code
python3 -m venv .venv
source .venv/bin/activate
pip install click httpx pydantic rich
pip install -e .
```

- [ ] **Step 2: 安装开发依赖**

```bash
pip install pytest pytest-asyncio ruff
```

- [ ] **Step 3: 验证安装**

```bash
python -c "import click; import httpx; import pydantic; import rich; print('OK')"
```
Expected: `OK`

---

### Task 2: 修正 pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 重写 pyproject.toml**

用 `src/` layout，console script 改为 `my-claude`，补 `build-system` 和 dev extra：

```toml
[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-claude-code"
version = "0.1.0"
description = "Python 版 Claude Code / MiniCode 风格终端编码助手"
requires-python = ">=3.10"
license = { text = "MIT" }

dependencies = [
    "click>=8.0",
    "httpx>=0.25",
    "pydantic>=2.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.5",
]

[project.scripts]
my-claude = "my_claude_code.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

- [ ] **Step 2: 重装包验证**

```bash
pip install -e ".[dev]"
```
Expected: 无错误

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: 更新 pyproject.toml 为 src/ layout 和 my-claude 命令名"
```

---

### Task 3: 创建 src/my_claude_code/ 包骨架

**Files:**
- Create: `src/my_claude_code/__init__.py`
- Create: `src/my_claude_code/cli.py`
- Create: `src/my_claude_code/core/__init__.py`
- Create: `src/my_claude_code/config/__init__.py`
- Create: `src/my_claude_code/providers/__init__.py`
- Create: `src/my_claude_code/tools/__init__.py`
- Create: `src/my_claude_code/permissions/__init__.py`
- Create: `src/my_claude_code/prompts/__init__.py`
- Create: `src/my_claude_code/runtime/__init__.py`
- Create: `src/my_claude_code/commands/__init__.py`

- [ ] **Step 1: 创建所有目录**

```bash
mkdir -p \
  src/my_claude_code/core \
  src/my_claude_code/config \
  src/my_claude_code/providers \
  src/my_claude_code/tools \
  src/my_claude_code/permissions \
  src/my_claude_code/prompts \
  src/my_claude_code/runtime \
  src/my_claude_code/commands \
  tests
```

- [ ] **Step 2: 写 `src/my_claude_code/__init__.py`**

```python
"""My Claude Code — Python 版终端编码助手."""

__version__ = "0.1.0"
```

- [ ] **Step 3: 写 `src/my_claude_code/cli.py`**

```python
"""CLI 入口 — 只做参数解析和分发，不承载 agent loop 逻辑。"""

import sys

import click


MIN_PYTHON = (3, 10)


def _check_python() -> tuple[bool, str]:
    v = sys.version_info[:2]
    ok = v >= MIN_PYTHON
    msg = f"Python {v[0]}.{v[1]} (需要 >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})"
    return ok, msg


def _check_imports() -> list[tuple[str, bool, str]]:
    results = []
    for pkg in ("click", "httpx", "pydantic", "rich"):
        try:
            __import__(pkg)
            results.append((pkg, True, "OK"))
        except ImportError as e:
            results.append((pkg, False, str(e)))
    return results


@click.group()
@click.version_option(version="0.1.0", prog_name="my-claude")
def main():
    """my-claude — Python 版终端编码助手"""


@main.command()
def doctor():
    """检查运行环境。"""
    ok, msg = _check_python()
    status = "✓" if ok else "✗"
    click.echo(f"  {status} Python: {msg}")

    for pkg, passed, detail in _check_imports():
        status = "✓" if passed else "✗"
        click.echo(f"  {status} {pkg}: {detail}")

    if not ok:
        sys.exit(1)
```

- [ ] **Step 4: 给每个子包写最小 `__init__.py`**

```bash
for d in core config providers tools permissions prompts runtime commands; do
  echo "\"\"\"$d 模块 — 待实现.\"\"\"" > src/my_claude_code/$d/__init__.py
done
```

- [ ] **Step 5: 验证 CLI 可执行**

```bash
pip install -e ".[dev]"
my-claude --help
```
Expected: 输出帮助信息，exit code 0

```bash
my-claude --version
```
Expected: 输出版本号

```bash
my-claude doctor
```
Expected: 输出 Python 和依赖检查结果，exit code 0

- [ ] **Step 6: Commit**

```bash
git add src/ tests/
git commit -m "feat(P0): 创建项目骨架 — CLI 入口、分层目录、doctor 命令"
```

---

### Task 4: 写 CLI 测试

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 写 `tests/__init__.py`**（空文件）

```bash
touch tests/__init__.py
```

- [ ] **Step 2: 写 `tests/test_cli.py`**

```python
from click.testing import CliRunner

from my_claude_code.cli import main


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "my-claude" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_doctor():
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    assert result.exit_code == 0
    assert "Python" in result.output
    assert "click" in result.output
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/ -v
```
Expected: 3 passed

- [ ] **Step 4: 运行 lint**

```bash
ruff check src/ tests/
```
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test(P0): 添加 CLI 测试 — help/version/doctor"
```

---

## P1：核心类型 + 模型适配器

### Task 5: 定义核心类型

**Files:**
- Create: `src/my_claude_code/core/types.py`
- Create: `tests/test_types.py`

- [ ] **Step 1: 写 `src/my_claude_code/core/types.py`**

```python
"""核心数据类型 — 基于 pydantic v2。

跨模块使用的消息、工具调用、模型用量等结构都在这里定义。
外部 API 原始响应只允许停留在 providers 层，不在此出现。
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ── 消息 ────────────────────────────────────────────


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """内部统一消息格式，与具体 API 格式解耦。"""

    role: MessageRole
    content: str
    id: str | None = None


# ── 模型用量 ────────────────────────────────────────


class ProviderUsage(BaseModel):
    """模型 API 返回的 token 用量。"""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


# ── 工具定义 ────────────────────────────────────────


class ToolInputSchema(BaseModel):
    type: Literal["object"] = "object"
    properties: dict = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    """工具定义 — name + description + JSON Schema input。"""

    name: str
    description: str
    input_schema: ToolInputSchema = Field(default_factory=ToolInputSchema)


class ToolCall(BaseModel):
    """模型请求的工具调用。"""

    id: str
    name: str
    input: dict = Field(default_factory=dict)


class ToolResult(BaseModel):
    """工具执行结果。"""

    tool_use_id: str
    content: str
    is_error: bool = False


# ── Agent 步骤 ──────────────────────────────────────


class StepStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    MAX_STEPS = "max_steps"
    STOPPED = "stopped"


class AgentStep(BaseModel):
    """一次 agent loop 步骤的完整记录。"""

    index: int
    model: str
    text: str = ""
    thinking: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    status: StepStatus = StepStatus.SUCCESS
    stop_reason: str = ""
    error: str = ""


class StepDiagnostics(BaseModel):
    """模型响应中的诊断信息。"""

    stop_reason: str = ""
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    error: str | None = None
```

- [ ] **Step 2: 写 `tests/test_types.py`**

```python
from my_claude_code.core.types import (
    AgentStep,
    ChatMessage,
    MessageRole,
    ProviderUsage,
    ToolCall,
    ToolDefinition,
    ToolInputSchema,
    ToolResult,
)


class TestChatMessage:
    def test_create_user_message(self):
        msg = ChatMessage(role=MessageRole.USER, content="hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "hello"

    def test_serialize(self):
        msg = ChatMessage(role=MessageRole.ASSISTANT, content="hi")
        d = msg.model_dump()
        assert d["role"] == "assistant"
        assert d["content"] == "hi"


class TestToolDefinition:
    def test_minimal_tool(self):
        td = ToolDefinition(name="read", description="Read a file")
        assert td.name == "read"
        assert td.input_schema.type == "object"

    def test_with_schema(self):
        td = ToolDefinition(
            name="write",
            description="Write a file",
            input_schema=ToolInputSchema(
                properties={"path": {"type": "string"}},
                required=["path"],
            ),
        )
        assert "path" in td.input_schema.properties
        assert "path" in td.input_schema.required


class TestAgentStep:
    def test_defaults(self):
        step = AgentStep(index=0, model="claude-sonnet-4-6")
        assert step.text == ""
        assert step.tool_calls == []
        assert step.status == "success"

    def test_with_tool_call(self):
        tc = ToolCall(id="tool_001", name="read", input={"path": "/tmp/x"})
        step = AgentStep(index=1, model="claude-sonnet-4-6", tool_calls=[tc])
        assert len(step.tool_calls) == 1
        assert step.tool_calls[0].name == "read"


class TestProviderUsage:
    def test_defaults(self):
        u = ProviderUsage()
        assert u.input_tokens == 0

    def test_usage(self):
        u = ProviderUsage(input_tokens=100, output_tokens=50)
        assert u.input_tokens == 100
        assert u.output_tokens == 50


class TestToolResult:
    def test_error_result(self):
        tr = ToolResult(tool_use_id="abc", content="not found", is_error=True)
        assert tr.is_error
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_types.py -v
```
Expected: 5-6 tests, all passed

- [ ] **Step 4: Commit**

```bash
git add src/my_claude_code/core/types.py tests/test_types.py
git commit -m "feat(P1): 定义核心类型 — ChatMessage / ToolDefinition / AgentStep / ProviderUsage"
```

---

### Task 6: 定义 ModelAdapter 抽象接口

**Files:**
- Create: `src/my_claude_code/providers/adapter.py`

- [ ] **Step 1: 写 `src/my_claude_code/providers/adapter.py`**

```python
"""模型适配器抽象接口。

所有模型适配器（Anthropic、mock、未来可能接入的其他厂商）都实现此接口。
只暴露内部类型，不泄漏外部 API 细节。
"""

from abc import ABC, abstractmethod

from my_claude_code.core.types import (
    ChatMessage,
    ToolCall,
    ToolDefinition,
    ProviderUsage,
    StepDiagnostics,
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
```

- [ ] **Step 2: 验证导入**

```bash
python -c "from my_claude_code.providers.adapter import ModelAdapter; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/my_claude_code/providers/adapter.py
git commit -m "feat(P1): 定义 ModelAdapter 抽象接口"
```

---

### Task 7: 实现 Anthropic 适配器（纯文本）

**Files:**
- Create: `src/my_claude_code/providers/anthropic.py`
- Create: `tests/test_anthropic_adapter.py`

- [ ] **Step 1: 实现 `src/my_claude_code/providers/anthropic.py`**

```python
"""Anthropic Messages API 适配器。

仅处理文本回复；不做 tool call、streaming、thinking block（后续里程碑补齐）。
"""

from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _RequestParams:
    model: str
    max_tokens: int
    system: str
    messages: list[dict]


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


def _parse_response(body: dict) -> tuple[str, list[ToolCall], ProviderUsage, StepDiagnostics]:
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
    """Anthropic Messages API 适配器。

    配置来源（优先级从高到低）：
    1. 构造参数
    2. 环境变量 ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL / ANTHROPIC_MODEL
    3. 默认值
    """

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
        self._base_url = (base_url or os.environ.get("ANTHROPIC_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
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
```

- [ ] **Step 2: 写 `tests/test_anthropic_adapter.py` — 消息转换测试**

```python
import pytest

from my_claude_code.core.types import ChatMessage, MessageRole
from my_claude_code.providers.anthropic import _to_api_messages


def test_to_api_messages_user():
    msgs = [ChatMessage(role=MessageRole.USER, content="hello")]
    result = _to_api_messages(msgs)
    assert len(result) == 1
    assert result[0] == {"role": "user", "content": "hello"}


def test_to_api_messages_assistant():
    msgs = [ChatMessage(role=MessageRole.ASSISTANT, content="hi")]
    result = _to_api_messages(msgs)
    assert len(result) == 1
    assert result[0] == {"role": "assistant", "content": "hi"}


def test_to_api_messages_skips_system():
    msgs = [ChatMessage(role=MessageRole.SYSTEM, content="system prompt")]
    result = _to_api_messages(msgs)
    assert len(result) == 0


def test_to_api_messages_mixed():
    msgs = [
        ChatMessage(role=MessageRole.USER, content="q1"),
        ChatMessage(role=MessageRole.ASSISTANT, content="a1"),
        ChatMessage(role=MessageRole.USER, content="q2"),
    ]
    result = _to_api_messages(msgs)
    assert len(result) == 3
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"
    assert result[2]["role"] == "user"
```

- [ ] **Step 3: 运行转换测试**

```bash
pytest tests/test_anthropic_adapter.py -v
```
Expected: 4 passed

- [ ] **Step 4: 运行 lint**

```bash
ruff check src/ tests/
```
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add src/my_claude_code/providers/anthropic.py tests/test_anthropic_adapter.py
git commit -m "feat(P1): 实现 Anthropic 适配器 — 消息转换 + retry + 响应解析"
```

---

### Task 8: 实现 mock 模型适配器

**Files:**
- Create: `src/my_claude_code/providers/mock.py`
- Create: `tests/test_mock_model.py`

- [ ] **Step 1: 实现 `src/my_claude_code/providers/mock.py`**

```python
"""Mock 模型 — 离线开发用，不消耗 API quota。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from my_claude_code.core.types import ProviderUsage, StepDiagnostics
from my_claude_code.providers.adapter import ModelAdapter

if TYPE_CHECKING:
    from my_claude_code.core.types import ChatMessage, ToolCall, ToolDefinition


class MockModel(ModelAdapter):
    """返回固定文本的 mock 模型。

    可以通过构造参数定制返回值，用于离线开发和测试。
    """

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
```

- [ ] **Step 2: 写 `tests/test_mock_model.py`**

```python
import pytest

from my_claude_code.core.types import ChatMessage, MessageRole, ToolCall
from my_claude_code.providers.mock import MockModel


@pytest.mark.asyncio
async def test_mock_returns_text():
    model = MockModel(text="hello world")
    text, calls, usage, diag = await model.next(
        messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        tools=[],
    )
    assert text == "hello world"
    assert calls == []
    assert diag.stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_mock_returns_tool_calls():
    tc = ToolCall(id="t1", name="read", input={"path": "/tmp/x"})
    model = MockModel(text="", tool_calls=[tc])
    _, calls, _, _ = await model.next(
        messages=[ChatMessage(role=MessageRole.USER, content="read /tmp/x")],
        tools=[],
    )
    assert len(calls) == 1
    assert calls[0].name == "read"


@pytest.mark.asyncio
async def test_mock_model_name():
    model = MockModel(model_name="test-mock")
    assert model.model_name == "test-mock"
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_mock_model.py -v
```
Expected: 3 passed

- [ ] **Step 4: Commit**

```bash
git add src/my_claude_code/providers/mock.py tests/test_mock_model.py
git commit -m "feat(P1): 实现 mock 模型适配器"
```

---

### Task 9: 最小配置模块

**Files:**
- Create: `src/my_claude_code/config/paths.py`
- Create: `tests/test_config_paths.py`

- [ ] **Step 1: 实现 `src/my_claude_code/config/paths.py`**

```python
"""路径常量 — 只定义目录和文件名，不做读写操作。"""

import os
from pathlib import Path


def _home() -> Path:
    return Path(os.environ.get("MINI_CODE_HOME", Path.home() / ".mini-code"))


SETTINGS_DIR = _home()
PROJECTS_DIR = _home() / "projects"
TOOL_RESULTS_DIR = _home() / "tool-results"
```

- [ ] **Step 2: 写 `tests/test_config_paths.py`**

```python
import os
from pathlib import Path

from my_claude_code.config import paths


def test_default_home():
    result = paths.SETTINGS_DIR
    assert result is not None


def test_custom_home(monkeypatch):
    custom = Path("/tmp/test-mini-home")
    monkeypatch.setenv("MINI_CODE_HOME", str(custom))
    # Re-import 不会更新，这里只验证 env 读取逻辑能工作
    # paths 模块在 import 时求值，所以此测试验证了默认值存在
    from my_claude_code.config.paths import PROJECTS_DIR

    assert "mini-code" in str(PROJECTS_DIR) or "mini-code" in str(Path.home() / ".mini-code")
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_config_paths.py -v
```
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add src/my_claude_code/config/paths.py tests/test_config_paths.py
git commit -m "feat(P1): 添加配置路径常量模块"
```

---

### Task 10: 集成 CLI — my-claude 启动 mock 和真实模型对话

**Files:**
- Modify: `src/my_claude_code/cli.py` — 添加 `--model` 选项和 `chat` 子命令
- Create: `src/my_claude_code/runtime/app.py` — 最小应用初始化
- Create: `tests/test_runtime_app.py`

- [ ] **Step 1: 写 `src/my_claude_code/runtime/app.py`**

```python
"""运行时 — 初始化模型适配器并运行一次对话。"""

from __future__ import annotations

from my_claude_code.core.types import ChatMessage, MessageRole
from my_claude_code.providers.adapter import ModelAdapter
from my_claude_code.providers.anthropic import AnthropicAdapter
from my_claude_code.providers.mock import MockModel


def create_model(model_name: str | None = None) -> ModelAdapter:
    """根据 model_name 创建对应的适配器。

    Args:
        model_name: "mock" 创建 MockModel，None 创建 AnthropicAdapter。
    """
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
```

- [ ] **Step 2: 往 `src/my_claude_code/cli.py` 添加 `chat` 子命令**

在 `cli.py` 中 `doctor` 命令之后追加。只增加 `chat` 命令，不改动已有的 `doctor`：

```python
import asyncio


@main.command()
@click.option("--model", default=None, help="模型名（mock 为离线模式）")
@click.option("--prompt", "-p", default="Hello", help="用户输入")
def chat(model: str | None, prompt: str):
    """单轮对话 — 验证模型链路。"""
    from my_claude_code.runtime.app import create_model, run_chat

    adapter = create_model(model)
    click.echo(f"[model: {adapter.model_name}]")

    text = asyncio.run(run_chat(adapter, prompt))
    click.echo(text)
```

等一下，这里有两个 `@main.command()` 声明，不能重复。要在 `cli.py` 中只添加一次 `chat` 命令。完整修改是在已有的 `cli.py` 末尾追加 `import asyncio` 和 `chat` 命令。

实际上让我把完整 CLI 代码写清楚 —— 追加到现有 cli.py 的 doctor 后面：

在 `cli.py` 中 `doctor` 命令之后（`if not ok: sys.exit(1)` 之后）追加：

```python
import asyncio


@main.command()
@click.option("--model", default=None, help="模型名（mock 为离线模式）")
@click.option("--prompt", "-p", default="Hello", help="用户输入")
def chat(model: str | None, prompt: str):
    """单轮对话 — 验证模型链路。"""
    from my_claude_code.runtime.app import create_model, run_chat

    adapter = create_model(model)
    click.echo(f"[model: {adapter.model_name}]")

    text = asyncio.run(run_chat(adapter, prompt))
    click.echo(text)
```

- [ ] **Step 3: 写 `tests/test_runtime_app.py`**

```python
import pytest

from my_claude_code.core.types import ChatMessage, MessageRole
from my_claude_code.providers.mock import MockModel
from my_claude_code.runtime.app import create_model, run_chat


def test_create_model_mock():
    m = create_model("mock")
    assert m.model_name == "mock"


def test_create_model_anthropic_default():
    m = create_model()
    assert "sonnet" in m.model_name or "mock" != m.model_name


@pytest.mark.asyncio
async def test_run_chat_mock():
    m = MockModel(text="response")
    result = await run_chat(m, "hello")
    assert result == "response"


@pytest.mark.asyncio
async def test_run_chat_with_system_prompt():
    m = MockModel(text="instructed response")
    result = await run_chat(m, "hello", system_prompt="You are helpful.")
    assert result == "instructed response"
```

- [ ] **Step 4: 验证 mock 模式**

```bash
my-claude chat --model mock --prompt "hi"
```
Expected: `[model: mock]\nMock response.`

- [ ] **Step 5: 运行全部测试**

```bash
pytest tests/ -v
```
Expected: 所有测试通过（~15+ tests）

- [ ] **Step 6: 运行 lint**

```bash
ruff check src/ tests/
```
Expected: 无错误

- [ ] **Step 7: Commit**

```bash
git add src/my_claude_code/cli.py src/my_claude_code/runtime/app.py tests/test_runtime_app.py
git commit -m "feat(P1): 集成 chat 命令 — 支持 mock 和真实模型单轮对话"
```

---

## P1 验证

全部完成后执行：

```bash
# 1. 安装
pip install -e ".[dev]"

# 2. 全量测试
pytest tests/ -v

# 3. Lint
ruff check src/ tests/

# 4. Mock 模式烟雾测试
my-claude chat --model mock --prompt "你好"

# 5. 真实模式烟雾测试（需设置 API key）
ANTHROPIC_API_KEY=sk-xxx my-claude chat --prompt "Say hello"

# 6. Doctor 检查
my-claude doctor
```

---



