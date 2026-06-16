/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 交易记录模块类型
 */

// GET /api/v1/trades?limit=N
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

// GET /api/v1/trades?page=&page_size= (分页响应)
export interface TradePage {
  data: Trade[]
  page: number
  page_size: number
  total: number
  total_pages: number
}
