/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: DashboardContext.tsx 全局状态与自动刷新
 * 描述: 全局状态管理，通过 useReducer 管理仪表盘数据，支持 HTTP 轮询和 WebSocket 实时推送
 *
 * 包含:
 * - 常量: initialState — 状态初始值，默认开启自动刷新
 * - 函数: reducer — 状态 reducer，处理 FETCH_START/FETCH_SUCCESS/FETCH_ERROR/TOGGLE_AUTO_REFRESH/WS_UPDATE 动作
 * - 类型: CtxValue — Context 值类型定义
 * - 组件: DashboardProvider — 状态提供者，封装状态管理和数据刷新逻辑
 * - Hook: useDashboard — 消费全局 Dashboard 状态的 Hook
 */
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

// Context 值类型 — 包含状态、刷新函数和自动刷新切换函数
interface CtxValue { state: DashboardState; refresh: () => void; toggleAutoRefresh: () => void }
const Ctx = createContext<CtxValue | null>(null)

// 状态提供者组件 — 管理 useReducer 状态、HTTP 轮询和 WebSocket 实时推送
export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  // 刷新函数 — 并发拉取 status/trades/equity 全量数据
  const refresh = useCallback(async () => {
    dispatch({ type: 'FETCH_START' })
    try {
      const data = await fetchAll()
      dispatch({ type: 'FETCH_SUCCESS', status: data.status, trades: data.trades, equity: data.equity })
    } catch (err: unknown) {
      dispatch({ type: 'FETCH_ERROR', error: err instanceof Error ? err.message : 'Unknown error' })
    }
  }, [])

  // 切换自动刷新开关
  const toggleAutoRefresh = useCallback(() => dispatch({ type: 'TOGGLE_AUTO_REFRESH' }), [])

  // 初始加载 — 组件挂载时立即拉取一次数据
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
      ws = new WebSocket(`${protocol}//${location.host}/ws/v1/live`)

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

// 消费全局 Dashboard 状态的自定义 Hook
export function useDashboard() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider')
  return ctx
}
