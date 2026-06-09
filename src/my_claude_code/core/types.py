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
