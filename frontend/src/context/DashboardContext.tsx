import { createContext, useContext, useReducer, useCallback, useEffect, type ReactNode } from 'react'
import type { DashboardState, DashboardAction } from '../types/dashboard'
import { fetchAll } from '../lib/api'

// 初始状态 — 自动刷新默认开启
const initialState: DashboardState = {
  status: null, trades: [], equity: [],
  loading: true, error: null,
  autoRefresh: true,  // 默认开启，页面看起来是活的
  lastUpdated: null,
}

function reducer(state: DashboardState, action: DashboardAction): DashboardState {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null }
    case 'FETCH_SUCCESS':
      return { ...state, loading: false, error: null, status: action.status,
        trades: action.trades, equity: action.equity, lastUpdated: Date.now() }
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.error }
    case 'TOGGLE_AUTO_REFRESH':
      return { ...state, autoRefresh: !state.autoRefresh }
    case 'WS_UPDATE':
      return { ...state, status: action.status, lastUpdated: Date.now() }
    default:
      return state
  }
}

interface CtxValue { state: DashboardState; refresh: () => void; toggleAutoRefresh: () => void }
const Ctx = createContext<CtxValue | null>(null)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const refresh = useCallback(async () => {
    dispatch({ type: 'FETCH_START' })
    try {
      const data = await fetchAll()
      dispatch({ type: 'FETCH_SUCCESS', status: data.status, trades: data.trades, equity: data.equity })
    } catch (err: unknown) {
      dispatch({ type: 'FETCH_ERROR', error: err instanceof Error ? err.message : 'Unknown error' })
    }
  }, [])

  const toggleAutoRefresh = useCallback(() => dispatch({ type: 'TOGGLE_AUTO_REFRESH' }), [])

  // 初始加载
  useEffect(() => { refresh() }, [refresh])

  // HTTP 轮询 — 5 秒间隔
  useEffect(() => {
    if (!state.autoRefresh) return
    const id = setInterval(refresh, 5000)
    return () => clearInterval(id)
  }, [state.autoRefresh, refresh])

  // WebSocket 实时推送
  useEffect(() => {
    let ws: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout>

    function connect() {
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
      ws = new WebSocket(`${protocol}//${location.host}/ws/live`)

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.type === 'tick_complete' && msg.btc_price) {
            // WebSocket 推送后立即 HTTP 拉全量（保证数据完整）
            refresh()
          }
        } catch { /* ignore */ }
      }

      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws?.close()
      }
    }

    connect()
    return () => {
      ws?.close()
      clearTimeout(reconnectTimer)
    }
  }, [refresh])

  return <Ctx.Provider value={{ state, refresh, toggleAutoRefresh }}>{children}</Ctx.Provider>
}

export function useDashboard() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider')
  return ctx
}
