# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目说明

详见 [AGENTS.md](./AGENTS.md)，此处只补充 Claude Code 专属内容。

## 硬性约束

- 不实现、不保留、不新增 mock provider、mock 模型、离线模型替身或 `--mock` 启动模式。
- 运行时只能接真实 provider；当前优先支持 Anthropic 与 DeepSeek/OpenAI-compatible。
- 单元测试可以用局部 fake/stub 验证纯逻辑，但测试替身不能进入运行时代码路径。
- 如代码、README、计划与本约束冲突，先修正文档和代码再继续实现。

## 技术选型

| 层 | 选型 |
|---|---|
| CLI | `click` |
| HTTP | `httpx` |
| Schema | `pydantic v2` |
| TUI | `rich` 起步，复杂交互用 `textual` |
| Diff | `difflib` (标准库) |
| 测试 | `pytest` + `pytest-asyncio` |
| 进程 | `asyncio.create_subprocess_exec` |
| 搜索 | 优先 `rg`，失败 fallback Python |
| 打包 | `pyproject.toml` |
| Lint | `ruff` |

## 参考源码

- Claude Code 源码分析：`/Users/jackson/文件/3_工作/code/claude-code-analysis/src`
- MiniCode TypeScript 源码：`/Users/jackson/文件/3_工作/code/MiniCode`
- 现有 MiniCode Python 版本：`/Users/jackson/文件/3_工作/code/python/MiniCode-Python`

## 当前规划

- 详细改写计划：`docs/MiniCode-python-rewrite-plan.md`
