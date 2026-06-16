/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 仪表盘模块类型定义
 * 包含系统运行状态、账户信息、市场行情、持仓、AI信号、全局状态等接口
 */

import type { Trade } from './trades'


// 账户信息
export interface AccountInfo {
  /** 账户余额（USDT） */
  balance: number
  /** 账户权益（余额 + 未实现盈亏） */
  equity: number
  /** 当前杠杆倍数 */
  leverage: number
}


// 行情快照
export interface MarketInfo {
  /** 当前最新价 */
  price: number
  /** 24小时涨跌幅（小数形式，如 0.05 表示 +5%） */
  change: number
  /** 当前K线周期，如 "1h", "5m" */
  timeframe: string
  /** 运行模式，如 "live" 实盘 / "paper" 模拟 / "backtest" 回测 */
  mode: string
}


// 持仓
export interface Position {
  side: 'long' | 'short'
  size: number
  entry_price: number
  unrealized_pnl: number
  mark_price: number
  pnl_pct: number
  margin: number
  notional: number
  liquidation_price: number
}


// 绩效统计
export interface Performance {
  /** 累计总盈亏 */
  total_pnl: number
  /** 胜率（0-1 之间的小数） */
  win_rate: number
  /** 累计成交笔数 */
  total_trades: number
}


// AI 信号
export interface AiSignal {
  /** 信号方向：买入 / 卖出 / 持仓不动 */
  signal: 'BUY' | 'SELL' | 'HOLD'
  /** 信号置信度 */
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'N/A'
  /** AI 给出该信号的推理依据 */
  reason: string
  /** 建议止损价 */
  stop_loss: number
  /** 建议止盈价 */
  take_profit: number
  /** 信号生成时间（ISO 字符串），null 表示暂无信号 */
  timestamp: string | null
}


// API 接口响应类型
/**
 * GET /api/v1/status 返回的完整系统状态
 */
export interface StatusData {
  /** 系统运行状态 */
  status: 'running' | 'stopped' | 'warning'
  /** 最后一次数据更新时间 */
  last_update: string | null
  /** 当前 Agent 模式: 5_agent | 3_agent | 1_agent | tech */
  agent_mode: string
  /** 账户信息 */
  account: AccountInfo
  /** 市场行情快照 */
  market: MarketInfo
  /** 当前持仓，若无则为 null */
  position: Position | null
  /** 绩效统计 */
  performance: Performance
  /** 最新 AI 信号 */
  ai_signal: AiSignal
}

/**
 * 权益曲线数据点
 * GET /api/v1/equity
 */
export interface EquityPoint {
  /** 时间戳（ISO 字符串） */
  timestamp: string
  /** 该时间点的账户权益 */
  equity: number
}

/**
 * K线数据点
 * GET /api/v1/kline
 */
export interface KlinePoint {
  /** K线开始时间（毫秒时间戳） */
  time: number
  /** 开盘价 */
  open: number
  /** 最高价 */
  high: number
  /** 最低价 */
  low: number
  /** 收盘价 */
  close: number
  /** 成交量 */
  volume: number
}


// 分页响应（通用）
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}


// Agent tick 日志（Redis 持久化，每 tick 一条）
export interface AgentTickLog {
  /** tick 时间戳 */
  ts: string
  /** 执行模式 */
  mode: string
  /** 各 Agent 的输出 */
  agents: Record<string, { output: string; handoff: string }>
}

// Agent 实时日志事件
export interface AgentEvent {
  /** 事件类型 */
  type: 'agent_input' | 'agent_output' | 'agent_tool_call'
  /** Agent 名称 */
  agent: string
  /** 时间戳（ISO 字符串） */
  ts: string
  /** 输入摘要（type=agent_input 时） */
  input?: string
  /** 输出摘要（type=agent_output 时） */
  output?: string
  /** 移交给哪个 Agent（type=agent_output 时） */
  handoff?: string
  /** 工具名称（type=agent_tool_call 时） */
  tool?: string
  /** 工具调用参数（type=agent_tool_call 时） */
  args?: string
  /** 工具调用结果（type=agent_tool_call 时） */
  result?: string
}

// 仪表盘全局状态 & 状态管理

/**
 * 仪表盘页面的完整状态树
 * 用于 React 状态管理（如 useReducer）
 */
export interface DashboardState {
  /** 系统实时状态数据 */
  status: StatusData | null
  /** 最近成交记录列表 */
  trades: Trade[]
  /** 权益曲线数据 */
  equity: EquityPoint[]
  /** 数据是否正在加载 */
  loading: boolean
  /** 错误信息，无错误时为 null */
  error: string | null
  /** 最后一次成功刷新数据的时间戳（毫秒） */
  lastUpdated: number | null
  /** Agent 实时日志（最新 30 条 WebSocket 事件） */
  agentEvents: AgentEvent[]
  /** Agent 历史日志（Redis 持久化，最近 5 轮 tick） */
  agentLogs: AgentTickLog[]
}

/**
 * 仪表盘状态 dispatch 动作类型
 * 用于 useReducer 的状态更新指令
 */
export type DashboardAction =
  | { type: 'LOADING' }                                               // 开始加载数据
  | { type: 'OK'; status: StatusData; trades: Trade[]; equity: EquityPoint[] }  // 数据加载成功
  | { type: 'ERROR'; error: string }                                 // 数据加载失败
  | { type: 'TICK' }                                                 // 定时刷新（可触发重新拉取）
  | { type: 'AGENT_EVENT'; event: AgentEvent }                       // Agent 实时日志推送
  | { type: 'AGENT_LOGS'; logs: AgentTickLog[] }                     // Agent 历史日志（API 加载）


// 健康检查


/**
 * GET /api/v1/health 返回的服务健康状态
 */
export interface HealthData {
  /** 服务是否正常运行 */
  ok: boolean
  /** 数据库类型或连接名，如 "postgres", "redis" */
  db: string
  /** 关键依赖是否已连接 */
  connected: boolean
  /** 如果未连接，返回具体错误原因 */
  error?: string
}
