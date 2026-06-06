import type { StatusData, Trade, EquityPoint } from '../types/dashboard'

const BASE = '/api'

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}
//
export async function fetchStatus(): Promise<StatusData> {
  return fetchJson<StatusData>(`${BASE}/status`)
}
//
export async function fetchTrades(limit = 20): Promise<Trade[]> {
  return fetchJson<Trade[]>(`${BASE}/trades?limit=${limit}`)
}
//
export async function fetchEquity(limit = 500): Promise<EquityPoint[]> {
  return fetchJson<EquityPoint[]>(`${BASE}/equity?limit=${limit}`)
}
//
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
