# P0 项目骨架计划：my-claude-code

## Summary

P0 目标是把仓库整理成“可运行空壳”：命名统一、Python 包可安装、CLI 可启动、分层目录就位、测试和 lint 能跑。

本阶段不实现 agent loop、模型调用、工具执行和权限逻辑，只为后续 P1-P5 铺好结构。

命名约定：

- 项目名：`my-claude-code`
- Python 包名：`my_claude_code`
- CLI 命令：`my-claude`
- 暂不保留 `minicode` 入口，避免品牌混乱。后续如需兼容可单独加 alias。

## Key Changes

### pyproject

- 更新 `[project].name = "my-claude-code"`。
- console script 改为 `my-claude = "my_claude_code.cli:main"`。
- 使用 `src/` layout：包放在 `src/my_claude_code/`。
- 增加 `build-system`。
- 增加 dev extra：
  - `pytest`
  - `pytest-asyncio`
  - `ruff`
- 保留运行依赖：
  - `click`
  - `httpx`
  - `pydantic`
  - `rich`

### 最小代码骨架

- 创建 `src/my_claude_code/__init__.py`，暴露 `__version__`。
- 创建 `src/my_claude_code/cli.py`，作为 Click CLI 入口。
- CLI 支持：
  - `my-claude --help`
  - `my-claude --version`
  - `my-claude doctor`
- `doctor` 只检查：
  - Python 版本。
  - 当前包可导入。
  - 基础依赖可导入。
- `doctor` 不启动模型、不读取真实 agent 配置、不写入任何配置文件。

### 阶段性目录

M1-M3 前先创建最小分层目录：

```text
src/my_claude_code/
  __init__.py
  cli.py
  core/
  config/
  providers/
  tools/
  permissions/
  prompts/
  runtime/
  commands/
```

每个目录只放 `__init__.py` 和必要的模块 docstring，不提前实现业务。

暂不创建：

- `sessions/`
- `context_management/`
- `tui/`
- `mcp/`
- `agents/`
- `hooks/`

这些目录在对应里程碑开始时再落地。

### 文档同步

- README 中的包名、命令名、安装命令、开发命令统一为 `my_claude_code` / `my-claude`。
- CLAUDE.md / AGENTS.md 记录命名规范。
- 规划文档 P0 标记为“建立可运行空壳”。
- 移除或修正旧 `mini_code` / `minicode` 入口表述。

## Test Plan

新增 `tests/test_cli.py`：

- `my_claude_code.cli` 可导入。
- Click runner 调用 `--help` 返回 0。
- Click runner 调用 `--version` 返回版本号。
- Click runner 调用 `doctor` 返回 0，并输出基础检查结果。

验收命令：

```bash
pip install -e ".[dev]"
my-claude --help
my-claude --version
my-claude doctor
pytest
ruff check src tests
```

## Assumptions

- P0 不实现真实配置读取、模型适配器、agent loop、工具注册或 TUI。
- P0 不创建 `sessions/`、`context_management/`、`tui/`、`mcp/`、`agents/`、`hooks/`。
- 旧规划里的 `mini_code` / `minicode` 都视为历史命名。
- P0 统一替换为 `my_claude_code` / `my-claude`。
