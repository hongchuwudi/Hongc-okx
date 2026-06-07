# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**语言偏好：请始终使用中文回复用户。**

## Project Overview

OKX 永续合约 AI 自动交易系统 (DOGE/USDT:USDT 默认)。5 Agent Swarm 架构 + DeepSeek V4-Flash + React 仪表盘。

**当前配置 (2026-06-07):**
- 交易对: DOGE/USDT:USDT
- 杠杆: 10x
- Tick: 6 分钟
- 止损: ATR × 0.8 (短线 0.3%~3%)
- 止盈: ATR × 1.5 (短线 0.6%~5%)
- 盈亏比: 2:1
- 模型: deepseek-v4-flash × 5
- 测试: 41 个全绿, 端到端 42s 通过

## Commands

```bash
# Backend: install dependencies
cd backend && pip install -r requirements.txt

# Backend: configure environment (required before running)
cd backend && cp .env_template .env
# Edit backend/.env with your DeepSeek API key, OKX API credentials, PostgreSQL and Redis connection info

# Backend: start API server + trading engine
cd backend && python run.py

# Frontend: dev server
cd frontend && npm install && npm run dev    # http://localhost:5173

# Frontend: build for production
cd frontend && npm run build

# API docs (when running)
# http://127.0.0.1:8765/docs
```

## Architecture

```
backend/
  run.py                  Unified launcher (FastAPI thread + TradingEngine asyncio)
  app/
    config/               Split config: postgres/redis/okx/ai/trade + AppConfig
    database/              Split: PG (sync+async) + Redis (pool+pubsub)
    logger.py             Logging module (console + rotating file)
    engine/loop.py        TradingEngine main loop, one tick per 6min
    exchange/             Split: base.py + okx/ (market/account/trade/setup) + client.py facade
    entities/             SQLAlchemy ORM: SystemStatus/Trade/EquitySnapshot/TradeMemory/BacktestRun/SystemConfig
    services/             MarketData/Risk/Scheduler/Strategy/Trade + ConfigService
    strategies/           TechnicalStrategy + DeepSeekStrategy
    agents/
      coordinator.py      5 Agent Swarm main pipeline (asyncio event-driven)
      agent_factory.py    5 Agent build logic (model+tool+prompt assembly)
      agent_logger.py     ToolCallLogger — intercept tool calls + push to status bus
      agent_status.py     Agent status bus — Redis Pub/Sub + in-memory for REST API
      models/             5 LLM instances: model_scheduler/analyst/reviewer/risk/trader
      prompts/            5 prompts: prompt_scheduler/analyst/reviewer/risk/trader
      toolkits/
        tools/            Pure calc: indicators/position/risk/memory/memory_private/feedback
        communication/    Swarm: handoff (transfer_to_X) + dialogue (ask_X) + router
        toolkit_*.py      Glue: lc_tool() wraps calc functions → exports tools=[]
      parser.py           JSON parser
      position_manager.py Dynamic trailing stop / TP-SL
    api/
      main.py             FastAPI v2.0 (CORS + static + routes)
      ws.py               WebSocket: Redis Pub/Sub → browser push
      routes/
        dashboard.py      /api/status, /api/health, /api/equity, /api/kline
        trades.py         /api/trades
        strategies.py     /api/strategies
        backtest.py       /api/backtest
        agents.py         /api/agents/status — Agent real-time status
        config.py         /api/config — dynamic config CRUD
    memory/store.py       MemoryStore — AI decision history
    backtest/engine.py    BacktestEngine
  legacy/                 v1.0 archive — NOT used
  tests/                  41 tests: calc/handoff/dialogue/memory/factory/integration/config/live

frontend/                 React 18 + TypeScript + Vite + ECharts
```

## Key Configuration

- **API keys**: `backend/.env` file — supports `AI_PROVIDER=deepseek` (default) or `AI_PROVIDER=qwen` (Alibaba DashScope)
  - DeepSeek: `DEEPSEEK_API_KEY` — platform.deepseek.com
  - Qwen/Alibaba: `DASHSCOPE_API_KEY` — dashscope.aliyun.com
  - OKX: `OKX_API_KEY`, `OKX_SECRET`, `OKX_PASSWORD`
- **Trading params**: `TradeConfig` dataclass in `backend/app/config.py` (symbol, leverage, timeframe, position sizing)
- **Risk params**: `MAX_DAILY_DRAWDOWN_PCT` and `MAX_DAILY_LOSS_USDT` in `backend/.env`
- **OKX sandbox**: `OKX_SANDBOX=true` → demo trading; set to `false` for real trading
- **Proxy**: `HTTPS_PROXY` in `.env` for servers in China to reach okx.com
- **Database**: PostgreSQL for persistent state + Redis for caching and Pub/Sub

## Important Patterns

- **4 Agent 决策架构**: `backend/app/agents/trade_graph.py` 定义 4 Agent 流水线：Phase1 调度师+分析师并行（ThreadPoolExecutor）→ Phase2 风控师 → 交易裁决员 → END。详见 `backend/app/agents/` 目录。
- **Agent 通信方式（重要局限）**: 当前 Agent 间通过共享 LangGraph State 字典通信，不是真正的消息传递。每个 Agent 从 state 读取上游输出、写入自己的结果，下游 Agent 自行挑选需要的字段。这是**多角色 Prompt Chain**，不是真正的多 Agent 系统。详见下方 [Known Gaps]。
- **Scheduling**: `SchedulerService` in `backend/app/services/scheduler.py` aligns ticks to wall-clock intervals.
- **Signal pipeline**: AgentCoordinator → Trade Graph (4 Agent) → RiskService check → PositionManager (dynamic TP/SL) → TradeService execution → persistence (PostgreSQL + Redis cache).
- **Dynamic position management**: `backend/app/agents/position_manager.py` runs every tick including HOLD — updates trailing stops and OKX algo orders based on unrealized PnL.
- **Persistence**: Each tick writes `SystemStatus` (upsert), `EquitySnapshot`, and optionally `Trade` to PostgreSQL, then refreshes Redis cache and publishes event to `ws:channel:updates`.
- **WebSocket**: `backend/app/api/ws.py` subscribes to Redis Pub/Sub and broadcasts to all connected browsers.
- **Frontend API compatibility**: `/api/trades` supports both `?limit=N` (flat array, used by frontend) and `?page=&page_size=` (paginated object).
- **Static files**: When `frontend/dist/` exists, `backend/app/api/main.py` serves the React app at `/`. In development, Vite dev server proxies `/api` to `localhost:8765`.
- **Startup cache cleanup**: `backend/run.py` 启动时自动清理 `__pycache__` 和 `.pyc`，防止旧字节码导致代码修改不生效。
- OKX exchange setup enforces **cross margin** + **one-way position mode**.
- Runtime-created directories: `data/` — created on startup for log files. Log file: `backend/trading_bot.log`.

## 命名规范（项目全局）

### 文件命名

- 使用**模块前缀**，类似 Redis 的 `redis-server` / `redis-cli` 风格
- 前缀 = 模块名，完整单词，**禁止缩写**
- 格式：`{模块名}_{功能描述}.py`

示例：
```
toolkit_data.py          ✓ 清晰
toolkit_calc_rsi.py      ✓ 清晰
tk_data.py               ✗ 缩写
data.py                  ✗ 无前缀，不知道属于哪个模块
```

### 目录命名

- 用完整单词，不用缩写
- 子模块的函数实现放 `tools/` 子目录
- 对外暴露的胶水层放模块根目录

```
toolkits/                ✓ 完整单词
├── tools/               ✓ 纯函数实现
│   └── toolkit_calc_*.py
├── toolkit_*.py         ✓ 胶水层，对外导出 tools = [...]
└── toolkit_data.py      ✓ 数据注入
```

### 变量/函数/类命名

- 函数：`snake_case`（`calc_rsi`、`get_position`）
- 类：`PascalCase`（`AgentCoordinator`、`TradeState`）
- 常量：`UPPER_SNAKE`（`MAX_RETRIES`）
- 私有函数：`_` 前缀（`_df()`、`_price()`）

### 导入规范

- 胶水层只能 import `lc_tool` + calc 函数
- calc 层只能 import `pandas` / `numpy` + `toolkit_data`
- 任何 `toolkits/` 下的文件不得引用 MCP / FastMCP

## Toolkits 规范

`backend/app/agents/toolkits/` 是所有 Agent 工具函数的管理目录。

### 文件命名

统一使用 `toolkit_` 前缀，禁止缩写：

```
toolkits/
├── toolkit_data.py              # 数据注入（load_data + _df/_price/_equity/_position 访问器）
├── toolkit_calc_indicator.py    # 纯计算：RSI、MACD、SMA、布林带、ATR、量比、趋势
├── toolkit_calc_position.py     # 纯计算：持仓、账户、浮动盈亏
├── toolkit_calc_risk.py         # 纯计算：风险评估、仓位上限、止损止盈
├── toolkit_calc_memory.py       # 纯查询：交易统计、历史记录、经验教训
├── toolkit_market.py            # 胶水层：lc_tool(toolkit_calc_indicator.*) → tools 列表
├── toolkit_position.py          # 胶水层：lc_tool(toolkit_calc_position.*) → tools 列表
├── toolkit_risk.py              # 胶水层：lc_tool(toolkit_calc_risk.*) → tools 列表
└── toolkit_memory.py            # 胶水层：lc_tool(toolkit_calc_memory.*) → tools 列表
```

### 三层架构（必须遵守）

```
┌─ toolkit_calc_*.py ──  纯 Python 计算函数，零框架依赖
│     可单独 import 测试，不引用 MCP / LangChain / LangGraph
│
├─ toolkit_*.py ────────  胶水层，用 lc_tool() 包装 calc 函数
│     只做一件事：from calc import fn → lc_tool(fn) → tools = [...]
│     禁止此层出现计算逻辑！
│
└─ coordinator.py ──────  从 toolkit_*.py import tools，传给 create_react_agent
     tools 走向：coordinator → create_react_agent → Agent 调 @tool → calc 执行
```

### 文件内容规范

**toolkit_calc_*.py（纯计算层）：**
- 只能 import `pandas` / `numpy` / `toolkit_data`
- 函数只做计算，返回 `str`
- 函数用 `def fn(args) -> str:` 带类型注解和 docstring
- 通过 `toolkit_data._df()` / `_price()` / `_equity()` / `_position()` 拿数据
- 不要在里面做格式美化，那是 Agent 的事

**toolkit_*.py（胶水层）：**
- 只 import 两样东西：`lc_tool` + calc 函数
- 每个 calc 函数 → `lc_tool(fn)` → 导出
- 最后汇总 `tools = [...]` 列表给 coordinator 用
- 禁止此层出现任何 import pandas/numpy/计算逻辑

**coordinator.py（消费层）：**
- `from app.agents.toolkits.toolkit_market import tools as mkt_tools`
- 把 tools 传给 `create_react_agent(tools=mkt_tools, ...)`
- 之后新增工具：在 calc 层加函数 → 在胶水层包装 → 在 coordinator 传入

### 新增工具的步骤

1. 在相应的 `toolkit_calc_*.py` 加纯计算函数
2. 在相应的 `toolkit_*.py` 加 `fn = lc_tool(calc_fn)` + 加入 `tools` 列表
3. 如果现有 tool 够用就不用改 coordinator

### 数据流

```
coordinator 每 tick:
  1. load_data(df, price, equity, position)  → 存入 toolkit_data 模块
  2. invoke(graph) → 4 个 Agent 子图按序执行
  3. Agent 在 ReAct 循环中自主决策调哪些 @tool
  4. @tool → calc 函数 → toolkit_data._df() → pandas 真实计算 → 返回字符串
```

## Known Gaps

当前 v2.0 已完成全部 Phase 1-3：

| 维度 | 状态 |
|------|:---:|
| 独立工具 + 真实计算 | ✅ toolkit_calc_*.py |
| Agent 互问 (transfer_to_X / ask_X) | ✅ toolkit_dialogue.py + toolkit_handoff.py |
| 风控退回重做 (最多2次) | ✅ coordinator.py _handle_asks + redo loop |
| PG 持久化私有记忆 (+ 内存降级) | ✅ toolkit_memory_private.py |
| 自适应准确率 (check_my_accuracy) | ✅ toolkit_memory_private.py |
| 学习闭环 (每 tick 反馈上一轮对错) | ✅ toolkit_calc_feedback.py |
| 状态总线 (Redis Pub/Sub → WebSocket) | ✅ agent_status.py + agent_logger.py |
| REST API (GET /api/agents/status) | ✅ api/routes/agents.py |
| 动态配置 (PG 存储 + API 修改) | ✅ services/config_service.py |

仍缺失: MCP 远程工具调用、前端 Agent 监控 UI、LangGraph Send API 自由对话。

## Git History (2026-06-07)

```
d62d6ed 优化: DOGE/USDT:USDT 默认交易对 + 短线参数 + 10x杠杆
1ed32ab 优化: 预注入行情数据, 225s→47s 5x提速
cabe60c 模型升级: deepseek-chat/reasoner → deepseek-v4-flash
63a4d2e 修复: 配置拆分后 .env 变量名对齐 + 新增配置验证测试
e42e1f2 新增: 集成测试 — Coordinator/移交/对话/反馈/退回
532ae10 新增: 测试框架 + 24 个测试用例全部通过
dc6db55 新增: 系统配置动态管理 (PG存储 + API修改)
db73e8d 拆分: config.py → config/ 子模块
a7d8e33 拆分: database.py → database/ 子模块
b52cd0f 拆分: exchange/client.py → okx/ 子模块
751b264 重命名: app/models/ → app/entities/ (ORM实体)
c1049de 规范: agent_logger/agent_status 移出 toolkits 目录
0c4bf8a 修复: agent_tool_call 接入状态总线
1260209 新增: Agent 状态总线 (Redis Pub/Sub → WebSocket)
90a1725 新增: GET /api/agents/status REST 接口
522706c 重构: 5 Agent Swarm 架构 (独立模型/线程/工具/记忆/通信)
```

## Comment Standards

每个文件头部必须有详细注释，格式如下：

**Python (.py) 文件:**
```python
"""
创建时间: YYYY-MM-DD
作者: hongchuwudi
描述: <一句话描述文件职责>

包含:
- 类: ClassName — <一句话描述>
- 函数: func_name — <一句话描述>
- 常量: CONST_NAME — <一句话描述>
- 变量: var_name — <一句话描述>
"""
```

**TypeScript/React (.tsx/.ts) 文件:**
```tsx
/**
 * 创建时间: YYYY-MM-DD
 * 作者: hongchuwudi
 * 描述: <一句话描述文件职责>
 *
 * 包含:
 * - 组件: ComponentName — <一句话描述>
 * - 函数: funcName — <一句话描述>
 * - 类型: TypeName — <一句话描述>
 * - 常量: CONST_NAME — <一句话描述>
 * - Hook: useHook — <一句话描述>
 */
```

**每个函数/类方法/变量/常量/类属性**需要一行注释说明其用途。
- Python: 使用 `#` 行注释
- TypeScript: 使用 `//` 行注释

## Security

- `backend/.env` (in `.gitignore`) contains real API keys and database passwords. Never commit it.
- The hardcoded cryptoracle.network API key in `backend/app/strategies/deepseek.py` should eventually be moved to `.env`.
