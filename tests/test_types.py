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
