"""路径常量 — 只定义目录名，不做读写操作。"""

import os
from pathlib import Path


def _home() -> Path:
    return Path(os.environ.get("MINI_CODE_HOME", Path.home() / ".mini-code"))


SETTINGS_DIR = _home()
PROJECTS_DIR = _home() / "projects"
TOOL_RESULTS_DIR = _home() / "tool-results"
