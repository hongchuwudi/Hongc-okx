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

- **Supervisor Agent Architecture**: `backend/app/agents/graph.py` defines a LangGraph StateGraph with Supervisor → {market, risk, memory} → Supervisor (loop) → trader → END. The Supervisor LLM dynamically decides which agents to call based on market state (ATR, volatility, position).
- **Scheduling**: `SchedulerService` in `backend/app/services/scheduler.py` aligns ticks to wall-clock intervals.
- **Signal pipeline**: AgentCoordinator → Supervisor Graph → Trader decision → PositionManager (dynamic TP/SL) → RiskService check → TradeService execution → persistence (PostgreSQL + Redis cache).
- **Dynamic position management**: `backend/app/agents/position_manager.py` runs every tick including HOLD — updates trailing stops and OKX algo orders based on unrealized PnL.
- **Persistence**: Each tick writes `SystemStatus` (upsert), `EquitySnapshot`, and optionally `Trade` to PostgreSQL, then refreshes Redis cache and publishes event to `ws:channel:updates`.
- **WebSocket**: `backend/app/api/ws.py` subscribes to Redis Pub/Sub and broadcasts to all connected browsers.
- **Frontend API compatibility**: `/api/trades` supports both `?limit=N` (flat array, used by frontend) and `?page=&page_size=` (paginated object).
- **Static files**: When `frontend/dist/` exists, `backend/app/api/main.py` serves the React app at `/`. In development, Vite dev server proxies `/api` to `localhost:8765`.
- OKX exchange setup enforces **cross margin** + **one-way position mode**.
- `backend/app/strategies/deepseek.py` contains a **hardcoded API key** (`7ad48a56-...`) for cryptoracle.network market sentiment. If that service is down, sentiment is silently skipped.
- Runtime-created directories: `data/` — created on startup for log files. Log file: `backend/trading_bot.log`.

## Security

- `backend/.env` (in `.gitignore`) contains real API keys and database passwords. Never commit it.
- The hardcoded cryptoracle.network API key in `backend/app/strategies/deepseek.py` should eventually be moved to `.env`.
