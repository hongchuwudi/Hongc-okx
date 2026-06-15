/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 仪表盘 API — 系统状态、健康检查、权益曲线、K线数据
 */

import { get, post } from '../utils/request'
import type { StatusData, HealthData, EquityPoint, KlinePoint, AgentTickLog } from '../types/dashboard'
import type { PaginatedResponse } from '../types/dashboard'

// 获取系统完整运行状态：账户余额/权益/杠杆、行情价格/涨跌、当前持仓、
// AI 交易信号（方向/置信度/止损止盈）、交易绩效（总盈亏/胜率/交易数）
export const fetchStatus = () => get<StatusData>('/status')

// 数据库连接健康检查：执行 SELECT 1 验证 PostgreSQL 连通性
export const fetchHealth = () => get<HealthData>('/health')

// 获取历史权益曲线数据点，limit 控制返回条数（1-2000）
// 返回 [{timestamp, equity}, ...]，供 ECharts 绘制权益走势图
export const fetchEquity = (limit = 500) => get<EquityPoint[]>(`/equity?limit=${limit}`)

// 获取 K 线 OHLCV 数据，symbol 为交易对（如 DOGE/USDT:USDT）
// timeframe 支持 1m/5m/30m/1h/4h/1d，limit 控制返回条数（1-500）
export const fetchKline = (symbol: string, timeframe = '1h', limit = 120) =>
  get<KlinePoint[]>(`/kline?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=${limit}`)

// 引擎开关控制
export const fetchEngineStatus = () =>
  get<{ running: boolean }>('/engine')

// Agent 历史日志（最近 N 轮 tick 的 agent 输出，?limit=5）
export const fetchAgentLogs = (limit = 5) =>
  get<AgentTickLog[]>(`/agents/logs?limit=${limit}`)

// Agent 日志分页查询
export const fetchAgentLogsPaginated = (page = 1, pageSize = 20) =>
  get<PaginatedResponse<AgentTickLog>>(`/agents/logs/paginated?page=${page}&page_size=${pageSize}`)

export const startEngine = () =>
  post<{ ok: boolean; message: string }>('/engine/start')

export const stopEngine = () =>
  post<{ ok: boolean; message: string }>('/engine/stop')

export const resetCircuit = () =>
  post<{ ok: boolean; message: string }>('/engine/reset-circuit')
