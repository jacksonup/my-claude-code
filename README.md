# My Claude Code

Python 版 Claude Code / MiniCode 风格终端编码助手。从零搭建，目标是充分理解 AI Agent 的核心架构。

## 快速开始：本地运行 DeepSeek

```bash
# 1. 创建虚拟环境（推荐 Python 3.10+）
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 配置 DeepSeek
export MY_CLAUDE_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-xxx

# 4. 检查、测试、启动
my-claude doctor
pytest
ruff check src tests
my-claude chat -p "你好，用一句话介绍你现在能做什么"
```

## 运行方式

| 命令 | 说明 |
|------|------|
| `my-claude doctor` | 检查 Python 与依赖 |
| `my-claude chat -p "你好"` | 使用当前配置的 provider 发起单轮真实模型调用 |
| `my-claude chat --provider deepseek -p "你好"` | 临时指定 DeepSeek |
| `my-claude chat --provider anthropic -p "你好"` | 临时指定 Anthropic |
| `my-claude --resume <session-id>` | 恢复历史会话 |
| `my-claude --fork <session-id>` | 分叉历史会话 |
| `my-claude mcp add/remove/list` | 管理 MCP 服务器 |
| `my-claude skills install/remove/list` | 管理 Skills |

## 配置模型

当前支持环境变量和本地用户配置文件：

- 环境变量：适合临时测试。
- 本地配置文件：`~/.my-claude-code/settings.json`，适合日常使用。

### 方式一：环境变量

DeepSeek：

```bash
export MY_CLAUDE_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-xxx
export DEEPSEEK_MODEL=deepseek-chat
my-claude chat -p "你好"
```

Anthropic：

```bash
export MY_CLAUDE_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-xxx
export ANTHROPIC_MODEL=claude-sonnet-4-6
my-claude chat -p "你好"
```

### 方式二：本地配置文件

```bash
mkdir -p ~/.my-claude-code
cat > ~/.my-claude-code/settings.json <<'JSON'
{
  "provider": "deepseek",
  "providers": {
    "deepseek": {
      "api_key": "sk-xxx",
      "model": "deepseek-chat",
      "base_url": "https://api.deepseek.com/v1"
    }
  }
}
JSON

my-claude chat -p "你好"
```

### 支持的环境变量

| 变量 | 说明 |
|------|------|
| `MY_CLAUDE_PROVIDER` | provider：`deepseek` / `anthropic` / `openai` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址，默认 `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | DeepSeek 模型名，默认 `deepseek-chat` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 |
| `ANTHROPIC_BASE_URL` | 自定义 API 地址（默认官方） |
| `ANTHROPIC_MODEL` | Anthropic 模型名，默认 `claude-sonnet-4-6` |
| `OPENAI_API_KEY` | OpenAI-compatible API 密钥 |
| `OPENAI_BASE_URL` | OpenAI-compatible API 地址 |
| `OPENAI_MODEL` | OpenAI-compatible 模型名 |
| `MY_CLAUDE_HOME` | 数据目录（默认 `~/.my-claude-code`） |
| `MY_CLAUDE_MAX_OUTPUT_TOKENS` | 最大输出 token 数 |

## 模块架构

```
src/my_claude_code/
├── cli.py                # CLI 入口，提供 my-claude 命令
├── core/                 # 消息、步骤、agent loop、运行事件
├── config/               # 路径、settings、MCP 配置、安装配置
├── providers/            # Anthropic / retry / usage
├── tools/                # 工具协议、注册表、内置工具
├── permissions/          # 权限模型、规则、command/path/edit policy
├── prompts/              # system prompt、协议说明、分层 prompt sections
├── runtime/              # app 初始化、turn runner、生命周期
├── commands/             # slash commands 和管理命令
├── sessions/             # 会话存储和 transcript（对应里程碑再创建）
├── context_management/   # token、大输出、压缩（对应里程碑再创建）
├── tui/                  # 终端 UI（对应里程碑再创建）
├── mcp/                  # MCP 客户端和动态能力（对应里程碑再创建）
├── agents/               # 多 Agent / AgentTool（对应里程碑再创建）
└── hooks/                # 工具生命周期 hooks（对应里程碑再创建）
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
source .venv/bin/activate
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check src tests

# 运行 DeepSeek
MY_CLAUDE_PROVIDER=deepseek DEEPSEEK_API_KEY=sk-xxx \
  my-claude chat -p "你好"
```

### 开发阶段

当前状态详见 [docs/MiniCode-python-rewrite-plan.md](./docs/MiniCode-python-rewrite-plan.md)，共分为 19 个模块（P0-P19），建议按以下顺序推进：

```
P0 项目骨架 → P1 真实模型文本闭环 → P2 真实工具调用闭环
→ P3 配置系统完善 → P4 最小工具系统
→ P5 Agent Loop 增强 → P6 文件编辑/权限/Review
→ P9 会话 → P10 Prompt/Memory/Skills
→ P7 Token → P8 压缩 → P11 Commands
→ P14 Hooks → P15 多 Agent → P16 Prompt 缓存
→ P12 TUI → P13 MCP → P17 Streaming Execution
→ P18 安装 → P19 测试补齐
```
