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

// 配置侧边栏字段元信息 — 描述每个配置项的展示和校验规则
export interface ConfigFieldMeta {
  key: string
  label: string
  type: 'select' | 'number'
  options?: { label: string; value: string }[]
  step?: number
  min?: number
  max?: number
  hint?: string
  instant: boolean  // true=即时生效，false=重启后生效
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
