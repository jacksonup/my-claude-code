import json

from my_claude_code.config import settings


def test_deepseek_from_user_settings(monkeypatch, tmp_path):
    config_dir = tmp_path / ".my-claude-code"
    config_dir.mkdir()
    settings_file = config_dir / "settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "provider": "deepseek",
                "providers": {
                    "deepseek": {
                        "api_key": "sk-deepseek",
                        "model": "deepseek-chat",
                        "base_url": "https://api.deepseek.com/v1",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(settings, "SETTINGS_FILE", settings_file)
    runtime = settings.load_runtime_settings()

    assert runtime.provider == "deepseek"
    assert runtime.api_key == "sk-deepseek"
    assert runtime.model == "deepseek-chat"
    assert runtime.base_url == "https://api.deepseek.com/v1"


def test_env_overrides_settings_provider(monkeypatch, tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"provider": "anthropic"}), encoding="utf-8")

    monkeypatch.setattr(settings, "SETTINGS_FILE", settings_file)
    monkeypatch.setenv("MY_CLAUDE_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env")

    runtime = settings.load_runtime_settings()

    assert runtime.provider == "deepseek"
    assert runtime.api_key == "sk-env"
