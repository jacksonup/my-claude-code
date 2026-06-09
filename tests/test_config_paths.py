from my_claude_code.config import paths


def test_default_home():
    assert paths.SETTINGS_DIR is not None
    assert "my-claude-code" in str(paths.SETTINGS_DIR)


def test_projects_dir():
    assert paths.PROJECTS_DIR.name == "projects"
