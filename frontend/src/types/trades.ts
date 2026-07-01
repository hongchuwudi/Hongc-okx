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

// GET /api/v1/trades/okx (OKX 真实成交记录)
export interface OkxTrade {
  id: string
  order_id: string
  timestamp: string
  symbol: string
  side: 'BUY' | 'SELL'
  price: number
  amount: number
  cost: number
  fee: number
  fee_currency: string
  role: string       // taker / maker
  type: string       // limit / market
  pnl: number        // OKX 返回的已实现盈亏
}

// OKX 成交分页响应
export interface OkxTradePage {
  data: OkxTrade[]
  total: number
  page: number
  page_size: number
  total_pages: number
  symbol: string
}
