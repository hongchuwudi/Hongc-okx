/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: dashboard.ts TypeScript类型定义
 * 描述: TypeScript 类型定义，描述后端 API 返回的完整数据结构，包含账户、行情、交易和状态
 *
 * 包含:
 * - 类型: AccountInfo — 账户余额/权益/杠杆信息
 * - 类型: BtcInfo — BTC 当前价格/涨跌幅/时间周期
 * - 类型: Position — 当前持仓信息
 * - 类型: Performance — 交易绩效统计
 * - 类型: AiSignal — AI 交易信号
 * - 类型: TpSlOrders — 止盈止损订单 ID
 * - 类型: StatusData — 系统整体状态
 * - 类型: Trade — 单笔交易记录
 * - 类型: EquityPoint — 权益曲线数据点
 * - 类型: DashboardState — 仪表盘全局状态
 * - 类型: DashboardAction — 状态管理动作联合类型
 */
// 账户信息 — 余额、权益、杠杆
export interface AccountInfo {
  balance: number
  equity: number
  leverage: number
}

// BTC 行情信息 — 价格、涨跌幅、时间周期、运行模式
export interface BtcInfo {
  price: number
  change: number
  timeframe: string
  mode: string
}

// 当前持仓信息 — 方向、数量、入场价、未实现盈亏
export interface Position {
  side: 'long' | 'short'
  size: number
  entry_price: number
  unrealized_pnl: number
}

// 交易绩效统计 — 总盈亏、胜率、总交易数
export interface Performance {
  total_pnl: number
  win_rate: number
  total_trades: number
}

// AI 交易信号 — 方向、置信度、理由、止盈止损价格
export interface AiSignal {
  signal: 'BUY' | 'SELL' | 'HOLD'
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'N/A'
  reason: string
  stop_loss: number
  take_profit: number
  timestamp: string
}

// 止盈止损订单 ID 映射
export interface TpSlOrders {
  stop_loss_order_id: string | null
  take_profit_order_id: string | null
}

// 系统整体状态 — 运行状态、账户、行情、持仓、绩效、AI 信号
export interface StatusData {
  status: 'running' | 'stopped' | 'warning'
  last_update: string
  account: AccountInfo
  btc: BtcInfo
  position: Position | null
  performance: Performance
  ai_signal: AiSignal
  tp_sl_orders?: TpSlOrders
  file_not_found?: boolean
}

// 单笔交易记录 — 时间、信号方向、价格、数量、盈亏等
export interface Trade {
  id: number
  timestamp: string
  signal: string
  price: number
  amount: number
  confidence: string
  reason: string
  pnl: number
}

// 权益曲线数据点
export interface EquityPoint {
  timestamp: string
  equity: number
}

// 仪表盘全局状态 — 含数据、加载状态、自动刷新和最后更新时间
export interface DashboardState {
  status: StatusData | null
  trades: Trade[]
  equity: EquityPoint[]
  loading: boolean
  error: string | null
  autoRefresh: boolean
  lastUpdated: number | null
}

// 状态管理动作联合类型
export type DashboardAction =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; status: StatusData; trades: Trade[]; equity: EquityPoint[] }
  | { type: 'FETCH_ERROR'; error: string }
  | { type: 'TOGGLE_AUTO_REFRESH' }
  | { type: 'MANUAL_REFRESH' }
  | { type: 'WS_UPDATE'; status: StatusData }
