# AGENTS.md

## 项目定位

本项目是一个从零搭建的 Python 版 Claude Code / MiniCode 风格终端编码助手。

所有功能设计都应优先参考 Claude Code 的设计理念，再结合 MiniCode 的轻量实现方式落地。目标不是机械翻译某一个仓库，而是搭出结构清晰、可维护、可逐步扩展的 Python 实现。

## 参考源码

- Claude Code 源码分析目录：`/Users/jackson/文件/3_工作/code/claude-code-analysis/src`
- MiniCode TypeScript 源码：`/Users/jackson/文件/3_工作/code/MiniCode`
- 现有 MiniCode Python 版本：`/Users/jackson/文件/3_工作/code/python/MiniCode-Python`

## 实现原则

- 可以参考、借鉴、复制现有 Python 版本中的实现，但需要重新整理结构，保持模块边界清晰。
- 功能设计优先对齐 Claude Code 的产品和交互理念。
- 工程实现优先参考 MiniCode 的轻量架构和可读性。
- 硬性约束：不实现、不保留、不新增 mock provider、mock 模型、离线模型替身或 `--mock` 启动模式。
- 单元测试可以用局部 fake/stub 验证纯逻辑，但这些测试替身不能进入运行时代码路径。
- 每次扩展功能时，先明确它属于 agent loop、tool system、permission、session、TUI、memory、skills、MCP 或 context management 中的哪一层。
- 保持文档和代码同步；新增关键模块时，补充对应说明。
- 单元测试只覆盖纯逻辑和转换逻辑；真实模型 API 行为放到显式集成测试中，通过环境变量启用。
- 每个核心模块至少一个测试文件，关注闭环而不是覆盖率数字。

## 文档索引

- Python 改写计划：`docs/MiniCode-python-rewrite-plan.md`
- P0 项目骨架计划：`docs/plan/P0-project-skeleton.md`
- 代码规范：`docs/engineering/code-standards.md`
