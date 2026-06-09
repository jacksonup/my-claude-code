import pytest

from my_claude_code.providers.mock import MockModel
from my_claude_code.runtime.app import create_model, run_chat


def test_create_model_mock():
    m = create_model("mock")
    assert m.model_name == "mock"


def test_create_model_anthropic_default():
    m = create_model()
    assert m.model_name == "claude-sonnet-4-6"


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
