/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 系统配置模块类型
 */

// GET /api/v1/config 或 /api/v1/config/runtime
export interface ConfigData {
  symbol: string
  leverage: number
  timeframe: string
  data_points: number
  tick_interval_seconds: number
  order_amount: number
  max_position_ratio: number
  max_daily_drawdown_pct: number
  max_daily_loss_usdt: number
  agent_auto_start: boolean
  agent_mode: string
  sandbox: boolean
}

// PUT /api/v1/config 或 /api/v1/config/runtime 请求体（所有字段可选）
export interface ConfigUpdate {
  symbol?: string
  leverage?: number
  timeframe?: string
  data_points?: number
  tick_interval_seconds?: number
  order_amount?: number
  max_position_ratio?: number
  max_daily_drawdown_pct?: number
  max_daily_loss_usdt?: number
  agent_auto_start?: boolean
  agent_mode?: string
  sandbox?: boolean
}
