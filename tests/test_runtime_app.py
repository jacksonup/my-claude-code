from my_claude_code.config.settings import RuntimeSettings
from my_claude_code.runtime.app import create_model, run_chat


def _settings(**kw) -> RuntimeSettings:
    defaults = {"provider": "anthropic", "model": "claude-sonnet-4-6",
                "api_key": "sk-test", "base_url": "https://api.anthropic.com"}
    return RuntimeSettings(**(defaults | kw))


def test_create_model_deepseek():
    m = create_model(_settings(provider="deepseek", model="deepseek-chat",
                                base_url="https://api.deepseek.com/v1"))
    assert m.model_name == "deepseek-chat"


def test_create_model_anthropic_default():
    m = create_model(_settings())
    assert m.model_name == "claude-sonnet-4-6"


def test_create_model_openai_custom():
    m = create_model(_settings(provider="openai", model="gpt-4o-mini",
                                base_url="https://api.openai.com/v1"))
    assert m.model_name == "gpt-4o-mini"


def test_create_model_missing_key_raises():
    import pytest
    with pytest.raises(RuntimeError, match="API key 未设置"):
        create_model(_settings(api_key=""))


class _TextOnlyModel:
    model_name = "test-model"

    async def next(self, messages, tools, system_prompt="", max_output_tokens=4096, **_):
        assert messages[0].content == "hello"
        assert tools == []
        assert max_output_tokens == 123
        from my_claude_code.core.types import ProviderUsage, StepDiagnostics
        return "response", [], ProviderUsage(), StepDiagnostics(stop_reason="end_turn")


async def test_run_chat_text_only():
    result = await run_chat(_TextOnlyModel(), "hello", max_output_tokens=123)
    assert result == "response"


class _ErrorModel:
    model_name = "error-model"

    async def next(self, messages, tools, system_prompt="", max_output_tokens=4096, **_):
        from my_claude_code.core.types import ProviderUsage, StepDiagnostics
        return "", [], ProviderUsage(), StepDiagnostics(error="boom")


async def test_run_chat_error_message():
    result = await run_chat(_ErrorModel(), "hello")
    assert result == "Error: boom"
