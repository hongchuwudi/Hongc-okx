/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 交易记录 API — 历史交易查询（扁平/分页两种模式）
 */

import { get } from '../utils/request'
import type { Trade, TradePage } from '../types/trades'

// 查询最近 N 条交易记录（扁平数组模式），按时间倒序
// limit 最大 500，前端仪表盘默认取 20 条用于最近交易列表
export const fetchTrades = (limit = 20) => get<Trade[]>(`/trades?limit=${limit}`)

// 分页查询交易记录，page 从 1 开始
// 返回 {data, page, page_size, total, total_pages}，适合大量历史数据浏览
export const fetchTradesPaged = (page = 1, pageSize = 20) =>
  get<TradePage>(`/trades?page=${page}&page_size=${pageSize}`)
