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
