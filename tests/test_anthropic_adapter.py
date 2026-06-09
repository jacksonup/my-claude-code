
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
