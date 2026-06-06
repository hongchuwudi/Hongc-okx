export interface AccountInfo {
  balance: number
  equity: number
  leverage: number
}

export interface BtcInfo {
  price: number
  change: number
  timeframe: string
  mode: string
}

export interface Position {
  side: 'long' | 'short'
  size: number
  entry_price: number
  unrealized_pnl: number
}

export interface Performance {
  total_pnl: number
  win_rate: number
  total_trades: number
}

export interface AiSignal {
  signal: 'BUY' | 'SELL' | 'HOLD'
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'N/A'
  reason: string
  stop_loss: number
  take_profit: number
  timestamp: string
}

export interface TpSlOrders {
  stop_loss_order_id: string | null
  take_profit_order_id: string | null
}

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

export interface EquityPoint {
  timestamp: string
  equity: number
}

export interface DashboardState {
  status: StatusData | null
  trades: Trade[]
  equity: EquityPoint[]
  loading: boolean
  error: string | null
  autoRefresh: boolean
  lastUpdated: number | null
}

export type DashboardAction =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; status: StatusData; trades: Trade[]; equity: EquityPoint[] }
  | { type: 'FETCH_ERROR'; error: string }
  | { type: 'TOGGLE_AUTO_REFRESH' }
  | { type: 'MANUAL_REFRESH' }
  | { type: 'WS_UPDATE'; status: StatusData }
