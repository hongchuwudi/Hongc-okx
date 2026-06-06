# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**语言偏好：请始终使用中文回复用户。**

## Project Overview

BTC/USDT perpetual futures auto-trading bot for OKX. Uses DeepSeek AI with a Supervisor multi-agent architecture (LangGraph StateGraph) to analyze OHLCV market data and generate trading signals (BUY/SELL/HOLD), executes trades with automatic algorithm stop-loss/take-profit orders, and serves a React web dashboard for real-time monitoring.

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
    config.py             Unified config from .env (Postgres, Redis, OKX, AI, Trade params)
    database.py           PostgreSQL (SQLAlchemy sync+async) + Redis connection pools
    logger.py             Logging module (console + rotating file)
    engine/loop.py        TradingEngine — event-driven main loop, one tick per minute
    exchange/client.py    OKX exchange client (CCXT wrapper)
    models/
      __init__.py         SQLAlchemy Base + re-exports
      system.py           SystemStatus — single-row table for current state
      trading.py          Trade + EquitySnapshot — trade records and equity history
      memory.py           TradeMemory — AI decision history for replay analysis
      backtest.py         BacktestRun — backtest execution records
    services/
      market_data.py      OHLCV, price, account, position fetching with Redis cache
      risk.py             Risk checks (daily drawdown, daily loss, circuit breaker)
      scheduler.py        Time-aligned tick scheduler
      strategy.py         StrategyService — strategy execution
      trade.py            TradeService — order execution with algo SL/TP
    strategies/
      base.py             BaseStrategy abstract class
      deepseek.py         DeepSeek AI strategy (technical indicators + market sentiment + LLM)
      technical.py        Technical indicator strategy (SMA + RSI + MACD)
    agents/
      coordinator.py      AgentCoordinator — thin wrapper, calls Supervisor graph
      graph.py            LangGraph StateGraph builder + router
      shared.py           SupervisorState TypedDict + LLM singleton
      schemas.py          Pydantic models (Signal, Confidence, AgentReport, TradeDecision)
      parser.py           Centralized JSON parser + AgentReport converter
      formats.py          Market/position/memory text formatters
      indicator_service.py  Unified technical indicator calculations
      position_manager.py   Dynamic trailing stop / TP-SL manager
      prompts/            One file per agent role:
        supervisor.py     Supervisor scheduling prompt
        market.py         Market analyst prompt
        risk.py           Risk manager prompt
        memory.py         Memory/replay analyst prompt
        trader.py         Final decision trader prompt
      nodes/              One file per LangGraph node:
        supervisor.py     supervisor_node — dynamic agent routing
        market.py         market_node — technical analysis
        risk.py           risk_node — risk assessment
        memory.py         memory_node — historical review
        trader.py         trader_node — final decision synthesis
    api/
      main.py             FastAPI app v2.0 (CORS, static files for production)
      ws.py               WebSocket manager — Redis Pub/Sub → browser real-time push
      routes/
        dashboard.py      /api/status, /api/health, /api/equity, /api/kline
        trades.py          /api/trades (flat array with ?limit= or paginated with ?page=&page_size=)
        strategies.py     /api/strategies (static strategy list)
        backtest.py       /api/backtest — backtest run + list + detail
    memory/
      store.py            MemoryStore — PostgreSQL-backed AI decision memory
    backtest/
      engine.py           BacktestEngine — historical data replay
  legacy/                 v1.0 monolithic archive (Streamlit + SQLite + JSON files)
                          See legacy/README.md — NOT used by current system

frontend/                 React 18 + TypeScript + Vite + ECharts dashboard
  src/
    App.tsx               Main dashboard layout
    context/              DashboardContext — global state + auto-refresh
    components/           PageHeader, KpiGrid, EquityChart, KlineChart,
                          AgentOffice, ActiveTradePanel, BacktestPanel, etc.
    lib/api.ts            API client (fetchStatus, fetchTrades, fetchEquity, fetchAll)
    types/dashboard.ts    TypeScript interfaces
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

## Known Gaps: 伪多 Agent → 真多 Agent 升级路线

> 注：Phase 1（工具独立化）已完成。每个 Agent 通过 `create_react_agent` + 真实计算的 @tool 实现 Function Calling。

### 现状（v2.0）

当前已完成：
- Agent 有独立工具 ✓（`toolkits/` 三层架构）
- 工具做真实计算 ✓（pandas/numpy，不读预计算缓存）
- 每个 Agent 有 React 循环 ✓（`create_react_agent` 的 ToolNode）

**仍缺失：**

| 维度 | 现状 | 真多 Agent 该有的 |
|------|------|-------------------|
| 通信 | 读写共享 State 字典 | Agent 间互相发消息/事件 |
| 路由 | 固定图结构 | 根据内容动态决定下一个找谁 |
| 记忆 | 每个 tick 从零开始 | 每个 Agent 有自己的持久化信念 |
| 退回 | 下游没法让上游重做 | 风控觉得分析师不足，可退回去要求重做 |

### 现状（v2.0）

当前架构本质是 **多角色 Prompt Chain**，不是真正的多 Agent：

```
N 个 LLM 调用 × 不同 system prompt × 共享一个 TypedDict
```

**缺失的核心能力：**

| 维度 | 现状 | 真多 Agent 该有的 |
|------|------|-------------------|
| 通信 | 读写共享 State 字典 | Agent 间互相发消息/事件，可指定接收者 |
| 对话 | 固定流水线，一次过 | 可多轮对话：A 问 B，B 答，A 不满意可追问 |
| 路由 | 固定图结构 | 根据对话内容动态决定下一个找谁 |
| 记忆 | 每个 tick 从零开始 | 每个 Agent 有自己的持久化信念，跨 tick 保留 |
| 工具 | 共用格式化文本 | 每个 Agent 自己调不同的工具/API |
| 退回 | 下游没法让上游重做 | 风控觉得分析师不足，可退回去要求重做 |
| 不同意 | 下游只能忽略上游 | 可显式驳回，记录分歧 |

### 升级路线（建议下次新会话实施）

**Phase 1: 工具独立化** — 每个 Agent 配自己的 tool
- 技术分析师调用 `calculate_rsi()`, `calculate_macd()` 等
- 环境分析师调用 `fetch_funding_rate()`, `fetch_volume_profile()`
- 形态分析师调用 `query_memory_store()` 查历史
- prompt 里去掉预先格式化的数据，改为让 Agent 自己调函数获取

**Phase 2: Agent 间消息通信** — 用 LangGraph Send API 或自建消息总线
- 替换 TypedDict → 消息对象（sender, receiver, content, type）
- Agent 可以主动 Push 消息给特定 Agent（不只是被动等下游读）
- 支持 request/reply 模式：A 向 B 提问题，B 回答后回传给 A

**Phase 3: 动态路由 + 信念持久化**
- 风控师可以退回分析师报告，触发"重做"边
- 每个 Agent 有自己的 SQLite/PG 表存信念状态
- 跨 tick 记忆："上轮我认为会涨，实际跌了，教训是..."

### 参考项目

搜索时发现的相关架构可参考：
- [NOFX](https://github.com/SkywalkerJi/nofx) — Web UI 策略构建器 + AI 辩论模式
- [Alpha Arena](https://github.com/AmadeusGB/alpha-arena) — 多 LLM 同条件 PK 对比框架
- [OKX Agent Trade Kit](https://github.com/okx/agent-trade-kit) — OKX 官方 MCP 协议工具包
- 百度开发者平台《基于 LangGraph 构建多智能体交易决策系统》— Send API 动态路由参考

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
