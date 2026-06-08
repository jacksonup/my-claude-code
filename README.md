# My Claude Code

Python 版 Claude Code / MiniCode 风格终端编码助手。从零搭建，目标是充分理解 AI Agent 的核心架构。

## 快速开始

```bash
# 1. 创建虚拟环境（推荐 Python 3.10+）
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 运行（mock 模式，不依赖真实模型）
minicode

# 4. 使用真实模型（需配置 API Key）
export ANTHROPIC_API_KEY=sk-xxx
minicode
```

## 运行方式

| 命令 | 说明 |
|------|------|
| `minicode` | 启动 CLI 对话（默认读 `ANTHROPIC_API_KEY`） |
| `MINI_CODE_MODEL_MODE=mock minicode` | Mock 模式，离线测试 |
| `minicode --resume <session-id>` | 恢复历史会话 |
| `minicode --fork <session-id>` | 分叉历史会话 |
| `minicode mcp add/remove/list` | 管理 MCP 服务器 |
| `minicode skills install/remove/list` | 管理 Skills |

## 环境变量

| 变量 | 说明 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 |
| `ANTHROPIC_BASE_URL` | 自定义 API 地址（默认官方） |
| `ANTHROPIC_MODEL` | 模型名（默认 `claude-sonnet-4-20250514`） |
| `MINI_CODE_MODEL_MODE` | `mock` 使用离线模拟模型 |
| `MINI_CODE_HOME` | 数据目录（默认 `~/.mini-code`） |
| `MINI_CODE_MAX_OUTPUT_TOKENS` | 最大输出 token 数 |

## 模块架构

```
mini_code/
├── cli.py               # CLI 入口
├── config.py             # 配置读写
├── types.py              # 核心数据类型
├── context.py            # 运行时上下文（ToolUseContext）
├── tool.py               # Tool 接口 + ToolRegistry
├── model_adapter.py      # ModelAdapter 抽象
├── anthropic_adapter.py  # Anthropic API 适配器
├── mock_model.py         # 离线 Mock 模型
├── agent_loop.py         # 主循环状态机
├── permissions.py        # 权限系统
├── file_review.py        # 文件修改 diff 审查
├── workspace.py          # 工作区路径管理
├── prompt.py             # System prompt 构建（含分层缓存）
├── tool_hooks.py         # Hook 系统 (Pre/PostToolUse)
├── streaming_executor.py # Streaming Tool Execution
├── memory.py             # 项目记忆加载
├── skills.py             # Skill 发现与加载
├── session.py            # 会话持久化
├── history.py            # 输入历史
├── tty_app.py            # TUI 主入口
├── mcp.py                # MCP 客户端
├── mcp_status.py         # MCP 状态汇总
├── cli_commands.py       # Slash 命令系统
├── local_tool_shortcuts.py # 本地快捷键命令
├── manage_cli.py         # 管理子命令
├── init.py               # 项目初始化
├── background_tasks.py   # 后台任务
├── install.py            # 安装脚本
│
├── tools/                # 内置工具
│   ├── list_files.py
│   ├── grep_files.py
│   ├── read_file.py
│   ├── write_file.py
│   ├── modify_file.py
│   ├── edit_file.py
│   ├── patch_file.py
│   ├── run_command.py
│   ├── web_fetch.py
│   ├── web_search.py
│   ├── ask_user.py
│   └── load_skill.py
│
├── compact/              # 上下文压缩
│   ├── microcompact.py
│   ├── snip_compact.py
│   ├── auto_compact.py
│   ├── context_collapse.py
│   └── manual_compact.py
│
├── agents/               # 多 Agent 定义
│   ├── __init__.py       #   AgentDefinition + AgentRegistry
│   ├── scheduler.py      #   runAgent() 生命周期管理
│   ├── general_purpose.py
│   ├── explore.py
│   └── verification.py
│
├── tui/                  # 终端 UI
│   ├── screen.py
│   ├── input_parser.py
│   ├── chrome.py
│   ├── transcript.py
│   ├── markdown.py
│   ├── permission_prompt.py
│   └── session_picker.py
│
└── utils/                # 工具函数
    ├── context.py
    ├── token_estimator.py
    ├── tool_result_storage.py
    ├── errors.py
    └── web.py
```

## 架构参考

本项目的架构设计参考了：

- **[Claude Code](https://code.claude.com/)** — Anthropic 官方终端编码助手，源码位于 `src/` 目录（1884 个 TypeScript 文件）
- **[MiniCode](https://github.com/nicepkg/minicode)** — 轻量级 terminal-first coding agent

核心设计理念：

1. **不信任模型的自觉性** — 好行为要写成制度，安全层互不绕过
2. **把角色拆开** — 实现者（GeneralPurpose）与验证者（Verification）分离
3. **工具调用要有治理** — 14 步执行 pipeline（校验 → hook → 权限 → 执行 → 后处理）
4. **上下文是预算** — 能缓存的不重算，能按需的不要一开始就塞进去
5. **产品化在于处理第二天** — 中断续接、脏状态清理、会话恢复

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check mini_code/

# 运行 mock 模式
MINI_CODE_MODEL_MODE=mock python -m mini_code.cli
```

### 开发阶段

当前状态详见 [docs/MiniCode-python-rewrite-plan.md](./docs/MiniCode-python-rewrite-plan.md)，共分为 19 个模块（P0-P19），建议按以下顺序推进：

```
P0 项目骨架 → P1 类型系统 → P2 配置 → P3 模型适配器
→ P4 基础工具 → P5 权限 → P6 Agent Loop
→ P9 会话 → P10 Prompt/Memory/Skills
→ P7 Token → P8 压缩 → P11 Commands
→ P14 Hooks → P15 多 Agent → P16 Prompt 缓存
→ P12 TUI → P13 MCP → P17 Streaming Execution
→ P18 安装 → P19 测试补齐
```
