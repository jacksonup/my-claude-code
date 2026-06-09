from my_claude_code.config.settings import RuntimeSettings
from my_claude_code.core.types import ChatMessage, MessageRole
from my_claude_code.providers.openai_compatible import (
    OpenAICompatibleAdapter,
    _to_chat_completion_messages,
)


def _openai_settings(**kw) -> RuntimeSettings:
    defaults = {"provider": "openai", "model": "gpt-4o",
                "api_key": "sk-test", "base_url": "https://api.openai.com/v1"}
    return RuntimeSettings(**(defaults | kw))


class TestToChatCompletionMessages:
    def test_user_message(self):
        msgs = [ChatMessage(role=MessageRole.USER, content="hello")]
        result = _to_chat_completion_messages(msgs)
        assert result == [{"role": "user", "content": "hello"}]

    def test_assistant_message(self):
        msgs = [ChatMessage(role=MessageRole.ASSISTANT, content="hi")]
        result = _to_chat_completion_messages(msgs)
        assert result == [{"role": "assistant", "content": "hi"}]

    def test_system_prompt_inserted_at_top(self):
        msgs = [ChatMessage(role=MessageRole.USER, content="q")]
        result = _to_chat_completion_messages(msgs, system_prompt="You are helpful.")
        assert result[0] == {"role": "system", "content": "You are helpful."}
        assert result[1] == {"role": "user", "content": "q"}

    def test_skips_system_messages(self):
        msgs = [ChatMessage(role=MessageRole.SYSTEM, content="sys")]
        result = _to_chat_completion_messages(msgs)
        assert len(result) == 0

    def test_mixed(self):
        msgs = [
            ChatMessage(role=MessageRole.USER, content="q1"),
            ChatMessage(role=MessageRole.ASSISTANT, content="a1"),
            ChatMessage(role=MessageRole.USER, content="q2"),
        ]
        result = _to_chat_completion_messages(msgs, system_prompt="s")
        assert len(result) == 4
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
        assert result[3]["role"] == "user"


def test_adapter_defaults():
    a = OpenAICompatibleAdapter(_openai_settings())
    assert a.model_name == "gpt-4o"


def test_adapter_custom_model():
    a = OpenAICompatibleAdapter(_openai_settings(model="deepseek-chat"))
    assert a.model_name == "deepseek-chat"
