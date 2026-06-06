/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: api.ts API客户端
 * 描述: API 客户端封装，提供后端 RESTful 接口的统一请求方法
 *
 * 包含:
 * - 函数: fetchJson — 通用 JSON 请求封装，含错误处理
 * - 函数: fetchStatus — 获取系统运行状态
 * - 函数: fetchTrades — 获取交易记录列表
 * - 函数: fetchEquity — 获取权益曲线数据
 * - 函数: fetchAll — 并发请求 status/trades/equity 全量数据
 */
import type { StatusData, Trade, EquityPoint } from '../types/dashboard'

const BASE = '/api'

// 通用 JSON 请求封装 — 自动处理 HTTP 错误状态
async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}
//
// 获取系统运行状态（账户、持仓、AI 信号等）
export async function fetchStatus(): Promise<StatusData> {
  return fetchJson<StatusData>(`${BASE}/status`)
}
//
// 获取交易记录列表，支持 limit 参数控制返回条数
export async function fetchTrades(limit = 20): Promise<Trade[]> {
  return fetchJson<Trade[]>(`${BASE}/trades?limit=${limit}`)
}
//
// 获取权益曲线数据，支持 limit 参数控制数据点数量
export async function fetchEquity(limit = 500): Promise<EquityPoint[]> {
  return fetchJson<EquityPoint[]>(`${BASE}/equity?limit=${limit}`)
}
//
// 并发拉取 status + trades + equity 全量数据，供仪表盘一次性刷新
export async function fetchAll(): Promise<{
  status: StatusData
  trades: Trade[]
  equity: EquityPoint[]
}> {
  const [status, trades, equity] = await Promise.all([
    fetchStatus(),
    fetchTrades(20),
    fetchEquity(500),
  ])
  return { status, trades, equity }
}
