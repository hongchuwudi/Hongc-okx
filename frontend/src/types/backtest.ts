/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 回测模块类型
 */

// POST /api/v1/backtest/run 请求体
export interface BacktestRunRequest {
  strategy: string
  symbol: string
  timeframe: string
  initial_capital: number
  position_ratio: number
  fee_rate: number
  warmup: number
  data_limit: number
  temperature: number
}

// GET /api/v1/backtest/runs 列表项
export interface BacktestRunItem {
  id: number
  strategy_name: string
  symbol: string
  timeframe: string
  data_count: number
  status: 'running' | 'completed' | 'failed'
  total_return_pct: number
  win_rate: number
  profit_factor: number
  max_drawdown_pct: number
  sharpe_ratio: number
  total_trades: number
  started_at: string | null
  finished_at: string | null
}

// 交易明细
export interface BacktestTrade {
  bar: number
  timestamp: string
  side: 'long' | 'short'
  entry: number
  exit?: number
  size: number
  pnl: number
  bars_held: number
  confidence: string
  action?: 'open' | 'close'
}

// GET /api/v1/backtest/runs/{id} 详情
export interface BacktestDetail {
  ok: boolean
  id: number
  strategy_name: string
  symbol: string
  timeframe: string
  data_count: number
  warmup: number
  status: string
  initial_capital: number
  final_equity: number
  total_return_pct: number
  win_rate: number
  profit_factor: number
  max_drawdown_pct: number
  sharpe_ratio: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  avg_trade_pnl: number
  started_at: string | null
  finished_at: string | null
  error_message: string | null
  trades: BacktestTrade[]
  equity_curve: { timestamp: number; equity: number }[]
}

// POST /api/v1/backtest/run 返回值
export interface BacktestRunResult {
  ok: boolean
  run_id: number
  metrics: Record<string, number>
  trades: BacktestTrade[]
  equity_curve: { timestamp: number; equity: number }[]
}

// SSE 流式事件类型
export interface BacktestProgressEvent {
  type: 'progress'
  bar: number
  total: number
  price: number
  equity: number
  signal: string
  confidence: string
  position_side: 'long' | 'short' | null
  trades_count: number
  timestamp: number
  trade: BacktestTrade | null
}

export interface BacktestDoneEvent {
  type: 'done'
  run_id?: number
  saved?: boolean
  trades: BacktestTrade[]
  equity_curve: { timestamp: number; equity: number }[]
  metrics: Record<string, number>
}

export interface BacktestErrorEvent {
  type: 'error'
  message: string
}

export type BacktestStreamEvent = BacktestProgressEvent | BacktestDoneEvent | BacktestErrorEvent
