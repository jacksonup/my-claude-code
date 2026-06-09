# MiniCode Python Rewrite Plan

本文档基于 TypeScript 版 MiniCode 的 README、架构说明和关键源码整理，用于指导 Python 版本改写。

MiniCode 的核心定位是一个轻量级 terminal-first coding agent。它不是完整 IDE 或大型 agent 平台，而是围绕 `model -> tool -> model` 闭环，提供终端交互、工具调用、权限审批、文件 review、会话持久化、上下文压缩、Skills 和 MCP 扩展。

## 1. 项目目标

Python 版本需要先复刻核心体验，再逐步补齐外围能力。

核心目标：

- 支持本地终端对话。
- 支持 Anthropic Messages API 兼容模型。
- 支持多步工具调用循环。
- 支持读写文件、搜索、编辑、命令执行等内置工具。
- 文件修改前生成 diff 并走审批。
- 会话按项目持久化，支持恢复。
- 支持本地 memory、skills、MCP。
- 支持长会话上下文统计、压缩和大工具输出落盘。
- 最终提供接近原项目的全屏 TUI。

## 2. 功能清单

### 2.1 CLI 启动与配置

- `my-claude` 命令入口。
- `--resume [session-id]` 恢复会话。
- `--fork <session-id>` 分叉会话。
- 管理子命令：
  - `my-claude mcp add/remove/list`
  - `my-claude skills install/remove/list`
  - `my-claude install`
- 配置读取：
  - `~/.my-claude-code/settings.json`
  - `~/.my-claude-code/mcp.json`
  - 项目 `.mcp.json`
  - 兼容 `~/.claude/settings.json`
- 环境变量覆盖：
  - `MY_CLAUDE_HOME`
  - `MY_CLAUDE_PROVIDER`
  - `MY_CLAUDE_MAX_OUTPUT_TOKENS`
  - `ANTHROPIC_MODEL`
  - `ANTHROPIC_BASE_URL`
  - `ANTHROPIC_AUTH_TOKEN`
  - `ANTHROPIC_API_KEY`
  - `DEEPSEEK_MODEL`
  - `DEEPSEEK_BASE_URL`
  - `DEEPSEEK_API_KEY`
  - `OPENAI_MODEL`
  - `OPENAI_BASE_URL`
  - `OPENAI_API_KEY`

### 2.2 Agent Loop

- 主循环执行 `model.next(messages)`。
- 支持 assistant 文本返回。
- 支持 progress 文本返回。
- 支持 tool calls。
- 执行工具后把 tool results 加回消息列表并继续模型调用。
- 支持空响应重试。
- 支持 thinking block 中断恢复。
- 支持最大工具步数限制。
- 支持 `ask_user` 工具触发 await-user 中断。
- 支持工具错误计数和友好错误提示。
- 每轮前运行上下文管理：
  - snip compact
  - microcompact
  - context collapse
  - auto compact

### 2.3 模型适配器

- 定义统一 `ModelAdapter` 接口。
- 实现 Anthropic Messages API 适配器。
- 转换内部消息到 Anthropic 格式：
  - system message -> 顶层 system 字段
  - user -> user text block
  - assistant -> assistant text block
  - assistant_progress -> `<progress>` text block
  - assistant_thinking -> thinking / redacted_thinking block
  - assistant_tool_call -> tool_use block
  - tool_result -> tool_result block
  - context_summary -> user text block
  - snip_boundary -> user text block
- 解析响应：
  - text block
  - tool_use block
  - thinking block
  - usage
  - stop_reason diagnostics
- 支持 retry：
  - HTTP 429
  - HTTP 5xx
  - `retry-after`
  - exponential backoff + jitter
- 不设计离线模型替身入口；早期闭环直接使用真实 provider，测试中只对纯函数和转换逻辑做离线验证。

### 2.4 工具系统

- 统一工具定义：
  - name
  - description
  - input_schema
  - pydantic schema
  - async run
- `ToolRegistry`：
  - `list`
  - `find`
  - `execute`
  - `add_tools`
  - `dispose`
- 内置工具：
  - `list_files`
  - `grep_files`
  - `read_file`
  - `write_file`
  - `modify_file`
  - `edit_file`
  - `patch_file`
  - `run_command`
  - `web_fetch`
  - `web_search`
  - `ask_user`
  - `load_skill`

### 2.5 权限与文件 Review

- cwd 内路径默认允许。
- cwd 外路径访问需要审批。
- 路径审批：
  - read
  - write
  - list
  - search
  - command_cwd
- 命令审批：
  - 识别危险命令。
  - 支持 allowlist / denylist。
  - 支持 session 级允许或拒绝。
- 编辑审批：
  - 写文件前生成 unified diff。
  - 用户可选择 allow once / allow always / allow turn / allow all turn / deny once / deny always / deny with feedback。
- 权限持久化：
  - `~/.my-claude-code/permissions.json`

### 2.6 TUI

- alternate screen。
- raw mode 输入。
- 顶部 banner。
- transcript 面板。
- 输入框。
- slash command menu。
- footer 状态栏。
- 工具执行状态。
- 权限审批 UI。
- 会话选择器。
- 输入历史。
- transcript 滚动。
- 鼠标文本选择。
- 自动复制选中文本。
- CJK 字符宽度处理。

### 2.7 会话系统

- 按项目隔离保存：
  - `~/.my-claude-code/projects/<project-name>/<session-id>.jsonl`
- append-only JSONL 事件流。
- 事件类型：
  - system
  - user
  - assistant
  - thinking
  - progress
  - tool_call
  - tool_result
  - summary
  - compact_boundary
  - snip_boundary
  - context_collapse
  - rename
- 支持：
  - save session
  - load session
  - load transcript
  - list sessions
  - rename session
  - fork session
  - clear session
  - cleanup expired sessions
  - list all projects

### 2.8 上下文管理

- provider usage 优先。
- 本地 token 估算作为 fallback。
- context warning level：
  - normal
  - warning
  - critical
  - blocked
- 压缩策略：
  - microcompact
  - snip compact
  - manual compact
  - auto compact
  - context collapse
- 大工具输出管理：
  - 超大 tool result 落盘到 `~/.my-claude-code/tool-results/`
  - prompt 中替换为预览和完整路径
  - 同一运行中稳定复用替换结果

### 2.9 Skills

- 扫描路径：
  - `.my-claude-code/skills/<name>/SKILL.md`
  - `~/.my-claude-code/skills/<name>/SKILL.md`
  - `.claude/skills/<name>/SKILL.md`
  - `~/.claude/skills/<name>/SKILL.md`
- 从 markdown 第一段提取描述。
- 同名 skill 按优先级取第一个。
- 支持：
  - list skills
  - load skill
  - install skill
  - remove skill

### 2.10 Memory

- 加载指令文件：
  - `MINI.md`
  - `MINI.local.md`
  - `.my-claude-code/MINI.md`
  - `CLAUDE.md`
  - `CLAUDE.local.md`
  - `.claude/CLAUDE.md`
  - `.my-claude-code/rules/*.md`
- 从 cwd 向上递归加载。
- 支持用户全局 memory。
- 支持 `@relative/path` include。
- 防止 include 绝对路径和 `..`。
- 内容去重。
- 单文件和总量截断。
- `/memory` 展示本轮加载文件。

### 2.11 MCP

- stdio MCP client。
- streamable HTTP MCP client。
- JSON-RPC 请求管理。
- 支持 content-length framing。
- 支持 newline-json framing。
- 协议探测和缓存。
- MCP initialize handshake。
- `tools/list` 和 `tools/call`。
- `resources/list` 和 `resources/read`。
- `prompts/list` 和 `prompts/get`。
- 动态包装为本地工具：
  - `mcp__<server>__<tool>`
- 动态注入资源和 prompt 工具：
  - `list_mcp_resources`
  - `read_mcp_resource`
  - `list_mcp_prompts`
  - `get_mcp_prompt`
- MCP server 状态汇总。

### 2.12 Slash Commands

- `/help`
- `/tools`
- `/status`
- `/model`
- `/model <name>`
- `/config-paths`
- `/skills`
- `/mcp`
- `/resume`
- `/resume <id>`
- `/rename <name>`
- `/new`
- `/fork`
- `/permissions`
- `/exit`
- `/ls [path]`
- `/grep <pattern>::[path]`
- `/read <path>`
- `/write <path>::<content>`
- `/modify <path>::<content>`
- `/edit <path>::<search>::<replace>`
- `/patch <path>::<search1>::<replace1>::...`
- `/cmd [cwd::]<command> [args...]`
- `/compact`
- `/collapse`
- `/snip`
- `/init`
- `/memory`

### 2.13 项目初始化

- `/init` 创建 `.my-claude-code/`。
- 更新 `.gitignore`。
- 生成 `MINI.md`。
- 检测语言和框架。
- 检测验证命令。
- 幂等执行。

## 3. Python 模块拆分

### 3.1 目录结构评审结论

原计划的主线是合理的，但根目录文件偏多，后期容易出现 `agent_loop.py`、`prompt.py`、`permissions.py`、`mcp.py`、`session.py` 这类文件持续膨胀的问题。

Claude Code 的源码分类更接近产品分层：

- `tools/`：每个工具独立目录或独立模块，工具协议与工具实现分离。
- `commands/`：slash command 独立成层，不混在 TUI 或 CLI 主循环里。
- `services/`：MCP、compact、session memory、API、plugins 等长期服务型能力独立管理。
- `components/` / `ink/`：UI 组件和终端渲染单独分层。
- `hooks/`：Hook 与权限回调不是工具的一部分，而是工具执行生命周期的一层。
- `tasks/` / `AgentTool`：多 agent、后台任务、子任务是运行时调度能力，不应塞进普通 tools。
- `constants/` / `schemas/` / `state/`：常量、schema、运行状态单独管理。

Python 版本建议保留 MiniCode 的轻量度，但吸收 Claude Code 的分层方式：根目录只放入口和少量聚合模块，复杂能力用 package 管理。

### 3.2 推荐目录结构 v2

```text
src/my_claude_code/
  __init__.py
  __main__.py               # python -m my_claude_code
  cli.py                    # 顶层 CLI 入口，仅负责参数分发和启动 runtime

  core/                     # 最核心协议，不依赖 UI / 具体 provider
    __init__.py
    messages.py             # ChatMessage / ProviderUsage / ThinkingBlock
    steps.py                # AgentStep / ToolCall / diagnostics
    context.py              # TurnContext / ToolUseContext / RuntimeContext
    agent_loop.py           # 主循环状态机
    events.py               # UI/CLI 可订阅的运行事件
    errors.py               # 核心异常类型

  config/                   # 配置和路径
    __init__.py
    paths.py                # MY_CLAUDE_HOME、settings/mcp/history/projects 路径
    settings.py             # settings.json / Claude fallback / env merge
    mcp_config.py           # user/project MCP 配置读写
    install.py              # 安装向导写配置

  providers/                # 模型 provider 适配层
    __init__.py
    base.py                 # ModelAdapter 抽象接口
    anthropic.py            # Anthropic Messages API
    retry.py                # 429/5xx retry、retry-after、jitter
    usage.py                # provider usage normalize

  tools/                    # 工具协议 + 内置工具
    __init__.py
    base.py                 # ToolDefinition / ToolResult / ToolContext
    registry.py             # ToolRegistry
    schemas.py              # 通用 schema helpers
    builtin.py              # 默认工具注册聚合
    filesystem/
      __init__.py
      list_files.py
      grep_files.py
      read_file.py
      write_file.py
      edit_file.py
      patch_file.py
      modify_file.py
      diff.py               # 文件 diff / review 相关纯逻辑
    shell/
      __init__.py
      run_command.py
      parser.py             # shell 命令解析、pipeline 检测
      background.py         # 后台 shell task 注册
    web/
      __init__.py
      fetch.py
      search.py
    skills/
      __init__.py
      load_skill.py
    user/
      __init__.py
      ask_user.py
    mcp_proxy/
      __init__.py
      tool_wrapper.py       # MCP tool -> 本地 ToolDefinition

  permissions/              # 权限与审批
    __init__.py
    manager.py              # PermissionManager
    models.py               # PermissionRequest / Decision / Choice
    rules.py                # allowlist / denylist / persistent store
    command_policy.py       # 危险命令分类
    path_policy.py          # cwd 边界、路径权限
    edit_policy.py          # edit diff 审批策略
    prompts.py              # 非 UI 的 permission prompt handler 协议

  hooks/                    # Claude Code 风格工具生命周期 Hook
    __init__.py
    models.py               # PreToolUse / PostToolUse / failure result
    registry.py             # HookRegistry
    matcher.py              # tool/path/command 匹配逻辑
    executor.py             # 执行 hooks 并合并结果

  prompts/                  # System prompt 和分层 prompt sections
    __init__.py
    system.py               # build_system_prompt
    sections.py             # systemPromptSections 风格切片
    protocol.py             # <progress> / <final> 协议说明
    memory_injection.py     # memory 渲染进 prompt
    templates.py            # compact/collapse 等 prompt 模板

  memory/                   # 项目指令 / memory 文件
    __init__.py
    discovery.py            # MINI.md / CLAUDE.md / rules 发现
    includes.py             # @path include 解析
    render.py               # 报告和 prompt 渲染

  skills/                   # SKILL.md 工作流
    __init__.py
    discovery.py
    loader.py
    installer.py
    models.py

  sessions/                 # 会话和 transcript
    __init__.py
    store.py                # JSONL append-only 存储
    events.py               # SessionEvent 类型和转换
    transcript.py           # transcript 重建
    listing.py              # list sessions/projects
    fork.py
    title.py                # 标题提取 / rename
    history.py              # 输入历史

  context_management/       # 上下文统计、压缩、大输出
    __init__.py
    token_estimator.py
    model_context.py
    tool_result_storage.py
    constants.py
    microcompact.py
    snip_compact.py
    manual_compact.py
    auto_compact.py
    context_collapse.py
    prompt.py

  mcp/                      # MCP 客户端和动态能力
    __init__.py
    client.py               # 抽象 MCP client
    stdio.py                # stdio JSON-RPC
    http.py                 # streamable HTTP
    framing.py              # content-length / newline-json
    protocol_cache.py
    resources.py
    prompts.py
    status.py
    tokens.py

  commands/                 # Slash commands 和管理命令，按命令分文件
    __init__.py
    registry.py
    parser.py
    slash.py
    local_tool_shortcuts.py
    help.py
    status.py
    model.py
    memory.py
    mcp.py
    skills.py
    session.py
    init.py
    compact.py
    permissions.py
    management.py           # my-claude mcp/skills/install 子命令

  workspace/                # 工作区相关能力
    __init__.py
    paths.py                # resolve tool path
    detect.py               # 项目语言/框架/验证命令检测
    init_project.py         # /init 创建 MINI.md / .gitignore

  runtime/                  # 应用运行时和执行器
    __init__.py
    app.py                  # 初始化 runtime：config/tools/provider/permissions
    turn_runner.py          # CLI/TUI 共用 turn 执行入口
    streaming_executor.py   # Streaming Tool Execution
    background_tasks.py
    lifecycle.py            # startup/shutdown/dispose

  agents/                   # 多 Agent / AgentTool / 子任务调度
    __init__.py
    models.py
    registry.py
    scheduler.py
    agent_tool.py
    builtins/
      general_purpose.py
      explore.py
      verification.py

  tasks/                    # 后台任务和长任务对象，区别于普通 tools
    __init__.py
    base.py
    local_shell.py
    local_agent.py

  tui/                      # 终端 UI
    __init__.py
    app.py                  # TUI 主循环
    state.py
    renderer.py
    screen.py
    input_parser.py
    input_buffer.py
    chrome.py
    transcript.py
    markdown.py
    permission_prompt.py
    session_picker.py
    tool_lifecycle.py
    theme.py

  services/                 # 可长期演进的服务型能力
    __init__.py
    api.py                  # provider API 低层 HTTP helper
    logging.py
    cost_tracker.py
    diagnostics.py

  constants/
    __init__.py
    files.py
    tools.py
    models.py
    prompts.py

  utils/                    # 纯工具函数，避免放业务逻辑
    __init__.py
    fs.py
    json.py
    text.py
    web.py
```

### 3.3 当前阶段可先落地的最小结构

为了避免过早工程化，M1-M3 阶段只需要先创建这些目录：

```text
src/my_claude_code/
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

`sessions/`、`context_management/`、`tui/`、`mcp/`、`agents/`、`hooks/` 可以在对应里程碑开始时再创建。

## 4. 开发任务拆分

### P0: 项目骨架

- [ ] 创建 `pyproject.toml`。
- [ ] 创建 `src/my_claude_code/__init__.py`。
- [ ] 创建 CLI 入口 `src/my_claude_code/cli.py`。
- [ ] 配置 console script：`my-claude = my_claude_code.cli:main`。
- [ ] 配置 pytest。
- [ ] 配置 ruff。
- [ ] 配置基础 README。

### P1: 真实模型文本闭环

目标：不接完整工具系统，先用真实 Anthropic provider 跑通 `user -> model -> final`。这是项目第一个核心可验证点。

- [ ] `src/my_claude_code/core/messages.py`
  - ChatMessage
  - ProviderUsage
  - ProviderThinkingBlock
- [ ] `src/my_claude_code/core/steps.py`
  - ToolCall
  - AgentStep
  - StepDiagnostics
  - CompressionResult
- [ ] `src/my_claude_code/tools/base.py` 和 `src/my_claude_code/tools/registry.py`
  - ToolContext
  - ToolResult
  - ToolDefinition
  - ToolRegistry
- [ ] `src/my_claude_code/providers/base.py`
  - ModelAdapter 抽象基类
- [ ] `src/my_claude_code/config/`
  - 读取 `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN`。
  - 读取 `ANTHROPIC_BASE_URL`。
  - 读取 `ANTHROPIC_MODEL`。
  - 未配置认证时给出清晰错误。
- [ ] `src/my_claude_code/providers/anthropic.py`
  - 最小 text-only Messages API 请求。
  - response text parse。
  - error message extract。
- [ ] `src/my_claude_code/core/agent_loop.py`
  - 主循环。
  - assistant final handling。
  - max step fallback。
  - 最小 callbacks：on_assistant_message。
- [ ] `tests/test_anthropic_message_conversion.py`
  - 内部 messages 可转换为 Anthropic request payload。
  - Anthropic text response 可转换为 assistant final。
- [ ] `tests/integration/test_real_text_loop.py`
  - 仅在存在 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN` 时运行。
  - 真实模型返回 assistant final。

### P2: 真实工具调用闭环

- [ ] `src/my_claude_code/runtime/app.py`
  - 创建 Anthropic provider。
  - 创建最小 ToolRegistry。
  - 创建初始 system/user messages。
  - 调用最小 agent loop。
- [ ] `src/my_claude_code/cli.py`
  - `my-claude "hello"` 或等价入口。
  - 打印 final assistant 内容。
  - 读取真实 provider 配置。
- [ ] `src/my_claude_code/tools/filesystem/list_files.py`
  - 真实低风险工具，用于首个 tool call roundtrip。
- [ ] `src/my_claude_code/tools/filesystem/read_file.py`
  - 真实低风险工具，用于读取明确路径。
- [ ] `src/my_claude_code/core/agent_loop.py`
  - tool call execution。
  - tool result 写回 messages。
- [ ] `tests/integration/test_real_tool_loop.py`
  - 仅在存在真实 Anthropic 认证时运行。
  - 模型可调用 `list_files` 或 `read_file`，然后返回 final。

### P3: 配置系统与 Anthropic 适配器完善

- [ ] `src/my_claude_code/config/`
  - 路径常量。
  - settings 文件读写。
  - MCP 配置文件读写。
  - scoped MCP 配置。
  - Claude settings fallback。
  - env override。
  - runtime config 校验。

- [ ] `src/my_claude_code/providers/anthropic.py`
  - 完整内部消息转 Anthropic 消息。
  - tools schema 转 Anthropic tools。
  - retry。
  - tool_use response parse。
  - usage normalize。

### P4: 最小工具系统

在 P2 的真实工具闭环验证通过后，再补齐更多真实只读/低风险工具。不急着做文件编辑和完整权限。

- [ ] `tools/list_files.py`
- [ ] `tools/grep_files.py`
- [ ] `tools/read_file.py`
- [ ] `tools/run_command.py`
- [ ] `tools/ask_user.py`
- [ ] `tools/web_fetch.py`
- [ ] `tools/load_skill.py`
- [ ] `tools/__init__.py` 注册默认工具。

### P5: Agent Loop 增强

- [ ] `src/my_claude_code/core/agent_loop.py`
  - progress handling。
  - empty response retry。
  - recoverable thinking retry。
  - await-user interrupt。
  - provider usage 附着。
  - tool result 大输出替换接入点。
  - 更完整 callbacks。

### P6: 文件编辑、权限和 Review

这一阶段再补写入类工具和安全边界。早期可以先用宽松策略跑通链路，等 agent loop 可测后再收紧审批。

- [ ] `tools/write_file.py`
- [ ] `tools/modify_file.py`
- [ ] `tools/edit_file.py`
- [ ] `tools/patch_file.py`
- [ ] `tools/web_search.py`

- [ ] `src/my_claude_code/permissions/`
  - PermissionManager。
  - path permission。
  - command permission。
  - edit permission。
  - allowlist / denylist。
  - turn-level approvals。
  - session-level approvals。
- [ ] `src/my_claude_code/tools/filesystem/diff.py`
  - build unified diff。
  - load existing file。
  - apply reviewed file change。
- [ ] `src/my_claude_code/workspace/`
  - path resolve。
  - cwd boundary。

### P7: Token 和大输出

- [ ] `utils/context.py`
  - model context window。
  - max output token resolve。
  - compactable tools。
- [ ] `utils/token_estimator.py`
  - estimate message tokens。
  - provider usage accounting。
  - mark usage stale。
  - context stats。
- [ ] `utils/tool_result_storage.py`
  - persisted output tags。
  - preview generation。
  - content replacement state。
  - per-result size limit。
  - batch budget。

### P8: 上下文压缩

- [ ] `compact/constants.py`
- [ ] `compact/microcompact.py`
- [ ] `compact/snip_compact.py`
- [ ] `compact/prompt.py`
- [ ] `compact/manual_compact.py`
- [ ] `compact/auto_compact.py`
- [ ] `compact/context_collapse.py`

### P9: 会话系统

- [ ] `src/my_claude_code/sessions/`
  - project dir name。
  - JSONL event append。
  - message id。
  - save session。
  - load session。
  - load transcript。
  - list sessions。
  - rename。
  - fork。
  - clear。
  - cleanup expired。
  - compact boundary。
  - snip boundary。
  - context collapse span。
- [ ] `src/my_claude_code/sessions/history.py`
  - input history append。
  - load history。
  - dedupe。

### P10: Prompt / Memory / Skills

- [ ] `src/my_claude_code/prompts/`
  - system prompt。
  - cwd。
  - progress/final protocol。
  - permission summary。
  - tools guidance。
  - skills list。
  - MCP status。
  - memory content。
- [ ] `src/my_claude_code/memory/`
  - instruction discovery。
  - include resolution。
  - dedupe。
  - truncation。
  - report rendering。
- [ ] `src/my_claude_code/skills/`
  - skill discovery。
  - load skill。
  - install skill。
  - remove skill。

### P11: Slash Commands 和管理命令

- [ ] `src/my_claude_code/commands/`
  - command list。
  - fuzzy match。
  - local command handling。
- [ ] `src/my_claude_code/commands/local_tool_shortcuts.py`
  - `/ls`
  - `/grep`
  - `/read`
  - `/write`
  - `/modify`
  - `/edit`
  - `/patch`
  - `/cmd`
- [ ] `src/my_claude_code/commands/management.py`
  - MCP add/remove/list。
  - skills install/remove/list。
- [ ] `src/my_claude_code/workspace/init_project.py`
  - project detection。
  - gitignore update。
  - MINI.md template。
  - init report。

### P12: TUI

- [ ] `tui/screen.py`
  - alternate screen。
  - raw mode。
  - cursor control。
  - terminal size。
- [ ] `tui/input_parser.py`
  - key events。
  - ctrl keys。
  - meta keys。
  - mouse events。
  - paste。
  - partial ANSI sequence buffer。
- [ ] `tui/chrome.py`
  - panel rendering。
  - color constants。
  - CJK width。
  - ANSI-aware wrap。
- [ ] `tui/transcript.py`
  - transcript entries。
  - render lines。
  - scroll window。
  - selection extraction。
- [ ] `tui/markdown.py`
  - terminal markdown rendering。
- [ ] `tui/permission_prompt.py`
  - permission request rendering。
  - option selection。
  - feedback mode。
- [ ] `tui/session_picker.py`
  - session list。
  - delete confirm。
  - all projects view。
- [ ] `src/my_claude_code/tui/app.py`
  - main TUI loop。
  - render layout。
  - input dispatch。
  - slash command handling。
  - permission mode。
  - session picker mode。
  - agent turn callbacks。

### P13: MCP

- [ ] `src/my_claude_code/mcp/`
  - stdio JSON-RPC client。
  - content-length framing。
  - newline-json framing。
  - protocol probe。
  - protocol cache。
  - streamable HTTP client。
  - tools list/call。
  - resources list/read。
  - prompts list/get。
  - MCP backed ToolDefinition factory。
- [ ] `src/my_claude_code/mcp/status.py`
  - summary counts。
  - status rendering data。

### P14: Hook 系统（对应 Claude Code toolHooks.ts）

- [ ] `src/my_claude_code/hooks/`
  - Hook 接口定义（PreToolUse / PostToolUse / PostToolUseFailure）
  - Hook 返回值类型：permissionBehavior / updatedInput / blockingError / additionalContexts
  - HookRegistry：注册、匹配、执行
  - resolveHookPermissionDecision()：Hook allow 不能绕过 settings deny
  - 生命周期管理：SubagentStart / Stop / SessionEnd

### P15: 多 Agent 调度（对应 Claude Code AgentTool + runAgent）

- [ ] `agents/__init__.py`
  - AgentDefinition 接口定义
  - AgentRegistry：注册、查找、过滤
- [ ] `agents/scheduler.py`
  - runAgent() 生命周期管理
  - 前台/后台/异步 任务模型
  - 清理链：MCP 连接、shell 进程、transcript、todos
- [ ] `agents/general_purpose.py`
  - 通用执行 Agent
- [ ] `agents/explore.py`
  - 只读探索 Agent（权限极端收紧，只能 Glob/Grep/Read）
- [ ] `agents/verification.py`
  - 验证 Agent（try to break it 理念）
- Fork 路径：继承父 system prompt，保持字节级一致复用 cache
- Agent 专属 MCP servers（frontmatter 配置）

### P16: Prompt 分层缓存（对应 Claude Code systemPromptSections）

整合到 `src/my_claude_code/prompts/` 内部，不拆成根目录单文件。具体机制：

- `systemPromptSection()`：首次计算后缓存，`/clear` 或 `/compact` 清除
- `DANGEROUS_uncachedSystemPromptSection()`：每轮重算（仅 MCP instructions 等需要）
- `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` 标记
- Section Registry：name + compute + cacheBreak 三元组管理
- 静态段（跨会话缓存）+ 动态段（按会话缓存）

### P17: Streaming Tool Execution（对应 Claude Code StreamingToolExecutor）

- [ ] `src/my_claude_code/runtime/streaming_executor.py`
  - 边收模型输出边执行已完成的 tool_use block
  - 工具结果按完成顺序回流

### P18: 安装与辅助模块

- [ ] `src/my_claude_code/config/install.py`
  - interactive install。
  - settings write。
  - launcher generation if needed。
- [ ] `src/my_claude_code/runtime/background_tasks.py`
  - register task。
  - list task。
  - track status。
- [ ] `utils/errors.py`
  - errno helpers。
- [ ] `utils/web.py`
  - fetch/search helpers。

### P19: 测试

测试规范：
- 使用 `pytest` + `pytest-asyncio`。
- 每个核心模块至少一个测试文件 `tests/test_<module>.py`。
- 单元测试不依赖真实模型 API 或网络；真实 provider 行为放在 `tests/integration/`，通过环境变量显式启用。
- 不设计离线 provider 替身；模型相关单元测试只覆盖 request/response 转换、错误解析和纯逻辑。
- 文件操作类测试用 `tmp_path` fixture，不要写真实目录。
- 关注核心闭环：消息转换、工具注册与执行、权限审批、会话持久化、压缩逻辑。
- TUI 不强制写自动化测试，但相关工具函数和状态机逻辑要达到覆盖率。

- [ ] types tests。
- [ ] tool registry tests。
- [ ] anthropic adapter conversion tests。
- [ ] tool tests。
- [ ] permission tests。
- [ ] file review tests。
- [ ] agent loop tests。
- [ ] token estimator tests。
- [ ] compact tests。
- [ ] session tests。
- [ ] memory tests。
- [ ] skills tests。
- [ ] slash command tests。
- [ ] input parser tests。
- [ ] transcript render tests。
- [ ] MCP tests。
- [ ] init tests。

## 5. 推荐开发顺序

建议不要一开始就做 TUI、MCP、完整权限和文件 review。先把真实模型文本闭环做通，再接真实低风险工具，让项目尽早进入可测试状态，后面再补安全边界和体验。

```text
P0 项目骨架
  -> P1 真实模型文本闭环
  -> P2 真实工具调用闭环
  -> P3 配置系统与 Anthropic 适配器完善
  -> P4 最小工具系统
  -> P5 Agent Loop 增强
  -> P6 文件编辑、权限和 Review
  -> P9 会话系统基础
  -> P10 Prompt / Memory / Skills
  -> P7 Token 和大输出
  -> P8 上下文压缩
  -> P11 Slash Commands
  -> P14 Hook 系统
  -> P15 多 Agent 调度层
  -> P16 Prompt 分层缓存（内聚到 prompt.py）
  -> P12 TUI
  -> P13 MCP
  -> P17 Streaming Tool Execution
  -> P18 安装与辅助模块
  -> P19 测试补齐
```

## 6. 里程碑

### M1: 可启动空壳

完成：

- `my-claude` 命令。
- `doctor`。
- 包可导入。
- pytest / ruff 可运行。

验收：

- `my-claude --help`、`my-claude --version`、`my-claude doctor` 均可运行。

### M2: 真实文本闭环可测试

完成：

- ChatMessage / AgentStep / ToolCall 基础类型。
- Anthropic text-only provider。
- agent loop 可执行 `user -> model -> final`。
- CLI 可触发真实模型调用。

验收：

- 配好 Anthropic 认证后，`my-claude "hello"` 可以返回真实 assistant final。

### M3: 真实工具调用闭环可测试

完成：

- list/read/grep。
- run_command。
- ask_user。
- tool call roundtrip 接入真实工具。

验收：

- 配好 token 后，模型可以请求读取文件、搜索文件、执行允许的命令，并基于工具结果继续回答。

### M4: 文件编辑闭环

完成：

- write/modify/edit/patch。
- unified diff。
- permission approval。

验收：

- 模型可以提出文件修改，用户 review diff 后应用。

### M5: 会话可恢复

完成：

- save/load/list session。
- resume。
- history。

验收：

- 退出后可恢复同一项目下的旧会话。

### M6: 项目上下文增强

完成：

- prompt。
- memory。
- skills。
- slash commands。
- `/init`。

验收：

- 项目 `MINI.md` 能进入 system prompt。
- `/memory` 能展示加载文件。
- `load_skill` 能返回 skill 内容。

### M7: 长上下文可用

完成：

- token estimator。
- tool result storage。
- microcompact。
- snip compact。
- manual/auto compact。
- context collapse。

验收：

- 大工具输出不会无限塞进 prompt。
- 长会话接近上下文限制时可以压缩。

### M8: TUI 可用

完成：

- transcript。
- input。
- slash menu。
- permission prompt。
- session picker。

验收：

- 交互体验接近 TypeScript 版本。

### M9: MCP 可用

完成：

- stdio MCP。
- HTTP MCP。
- tool/resource/prompt wrappers。
- `/mcp` 状态。

验收：

- 能接入一个 MCP server 并调用其工具。

## 7. Python 技术选型

| 层 | 推荐 |
| --- | --- |
| CLI | `click` |
| HTTP | `httpx` |
| Schema | `pydantic v2` |
| TUI | `rich` 起步，复杂交互可用 `textual` |
| Diff | `difflib` |
| Tests | `pytest` + `pytest-asyncio` |
| Process | `asyncio.create_subprocess_exec` |
| Search | 优先调用 `rg`，失败后 fallback 到 Python 遍历 |
| Packaging | `pyproject.toml` |

## 8. 架构参考来源

### Claude Code 源码对照

| Claude Code 文件 | Python 模块 | 说明 |
|---|---|---|
| `query.ts` (1729行) — 主循环状态机 | `src/my_claude_code/core/agent_loop.py` | while(true) + 9 种 continue 原因 |
| `Tool.ts` (792行) — 工具基类 | `src/my_claude_code/tools/base.py` | fail-closed 默认值设计 |
| `toolExecution.ts` (1745行) — 14 步 pipeline | `src/my_claude_code/tools/registry.py` + `src/my_claude_code/hooks/` | 校验 → hook → 权限 → 执行 → 后处理 |
| `toolHooks.ts` — Hook 系统 | `src/my_claude_code/hooks/` | PreToolUse / PostToolUse / PostToolUseFailure |
| `prompts.ts` (914行) + `systemPromptSections.ts` | `src/my_claude_code/prompts/` | 分层 prompt 缓存范式 |
| `AgentTool.tsx` (1397行) + `runAgent.ts` (973行) | `src/my_claude_code/agents/` | 多 Agent 调度体系 |
| `StreamingToolExecutor.ts` | `src/my_claude_code/runtime/streaming_executor.py` | 边收边跑 |
| `memdir/` (10文件) — 记忆系统 | `src/my_claude_code/memory/` | 增量写入 + 双模型召回 |
| `services/compact/` (11文件) | `src/my_claude_code/context_management/` | 四层压缩栈 |
| `utils/permissions/` (27文件) | `src/my_claude_code/permissions/` | 三层互不绕过防护网 |

### MiniCode 源码对照

| MiniCode TS 文件 | Python 模块 |
|---|---|
| `src/index.ts` | `src/my_claude_code/cli.py` + `src/my_claude_code/runtime/app.py` |
| `src/config.ts` | `src/my_claude_code/config/` |
| `src/types.ts` | `src/my_claude_code/core/messages.py` + `src/my_claude_code/core/steps.py` |
| `src/tool.ts` | `src/my_claude_code/tools/base.py` + `src/my_claude_code/tools/registry.py` |
| `src/agent-loop.ts` | `src/my_claude_code/core/agent_loop.py` |
| `src/anthropic-adapter.ts` | `src/my_claude_code/providers/anthropic.py` |
| `src/permissions.ts` | `src/my_claude_code/permissions/` |
| `src/file-review.ts` | `src/my_claude_code/tools/filesystem/diff.py` |
| `src/workspace.ts` | `src/my_claude_code/workspace/` |
| `src/prompt.ts` | `src/my_claude_code/prompts/` |
| `src/session.ts` | `src/my_claude_code/sessions/` |
| `src/history.ts` | `src/my_claude_code/sessions/history.py` |
| `src/memory.ts` | `src/my_claude_code/memory/` |
| `src/skills.ts` | `src/my_claude_code/skills/` |
| `src/mcp.ts` | `src/my_claude_code/mcp/` |
| `src/mcp-status.ts` | `src/my_claude_code/mcp/status.py` |
| `src/cli-commands.ts` | `src/my_claude_code/commands/` |
| `src/local-tool-shortcuts.ts` | `src/my_claude_code/commands/local_tool_shortcuts.py` |
| `src/manage-cli.ts` | `src/my_claude_code/commands/management.py` |
| `src/init.ts` | `src/my_claude_code/workspace/init_project.py` |
| `src/background-tasks.ts` | `src/my_claude_code/runtime/background_tasks.py` |
| `src/tty-app.ts` | `src/my_claude_code/tui/app.py` |
| `src/tools/*` | `src/my_claude_code/tools/*` |
| `src/compact/*` | `src/my_claude_code/context_management/*` |
| `src/tui/*` | `src/my_claude_code/tui/*` |
| `src/utils/*` | `src/my_claude_code/utils/*` |

说明：P14-P17（Hook 系统、多 Agent 调度、Prompt 分层缓存、Streaming Execution）是 MiniCode 原版不包含的设计，参考 Claude Code 源码补充。这些模块在 MiniCode 中没有对应文件。

## 9. 实施建议

优先保证核心闭环，而不是逐文件机械翻译。

第一阶段建议只追求：

- 普通 CLI。
- Anthropic adapter。
- ToolRegistry。
- read/list/grep/run_command。
- Agent loop。

这个阶段完成后，项目就已经具备 coding agent 的最小可用形态。

第二阶段再加入：

- 文件编辑。
- diff review。
- permissions。
- session resume。
- memory。
- skills。

第三阶段补齐：

- TUI。
- context compression。
- MCP。

这样可以避免一开始被 TUI、MCP、上下文压缩这些大模块拖住主线。
