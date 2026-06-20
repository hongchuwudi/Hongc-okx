/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 交易记录 API — 系统数据库记录 + OKX 真实成交
 *
 * 包含:
 * - fetchTrades          — 查询最近 N 条系统交易记录（扁平数组）
 * - fetchTradesPaged     — 分页查询系统交易记录
 * - fetchOkxTrades       — 分页查询 OKX 真实成交（含方向/时间筛选）
 */

import { get } from '../utils/request'
import type { Trade, TradePage, OkxTradePage } from '../types/trades'

// 查询最近 N 条系统交易记录，按时间降序
// limit 最大 500，仪表盘默认取 20 条显示最近交易列表
export const fetchTrades = (limit = 20) => get<Trade[]>(`/trades?limit=${limit}`)

// 分页查询系统数据库交易记录，page 从 1 开始
// 返回 { data, page, page_size, total, total_pages }
export const fetchTradesPaged = (page = 1, pageSize = 20) =>
  get<TradePage>(`/trades?page=${page}&page_size=${pageSize}`)

// 分页查询 OKX 真实成交记录
// 支持 direction/side 筛选、时间范围过滤
export interface OkxTradesParams {
  symbol?: string
  limit?: number
  page?: number
  pageSize?: number
  side?: 'buy' | 'sell'
  startTime?: string
  endTime?: string
}

export const fetchOkxTrades = (params: OkxTradesParams = {}) => {
  const {
    symbol = 'DOGE/USDT:USDT',
    limit = 100,
    page = 1,
    pageSize = 20,
    side,
    startTime,
    endTime,
  } = params

  let url = `/trades/okx?symbol=${encodeURIComponent(symbol)}&limit=${limit}&page=${page}&page_size=${pageSize}`
  if (side) url += `&side=${side}`
  if (startTime) url += `&start_time=${encodeURIComponent(startTime)}`
  if (endTime) url += `&end_time=${encodeURIComponent(endTime)}`

  return get<OkxTradePage>(url)
}
