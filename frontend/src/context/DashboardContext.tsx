/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 仪表盘全局状态 — HTTP 轮询 + WebSocket 推送
 */

/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 仪表盘全局状态 — HTTP 轮询 + WebSocket 推送
 *
 * 包含:
 * - DashboardProvider — Context Provider，管理定时轮询和 WS 连接
 * - useDashboard — 消费 Hook，组件内获取 state 和 refresh
 * - reducer — 处理 LOADING / OK / ERROR / TICK 四种状态转换
 */
import { createContext, useContext, useReducer, useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import type { DashboardState, DashboardAction, AgentEvent } from '../types/dashboard'
import { fetchStatus, fetchEquity, fetchAgentLogs } from '../api/dashboard'
import { fetchTrades } from '../api/trades'
import { connectWs } from '../utils/ws'

// 初始状态：未加载，无数据
const init: DashboardState = {
  status: null, trades: [], equity: [],
  loading: true, error: null, lastUpdated: null,
  agentEvents: [],
  agentLogs: [],
}

/** 从数组尾部向前查找匹配元素的位置 */
function findLastIndex<T>(arr: T[], predicate: (item: T) => boolean): number {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (predicate(arr[i])) return i
  }
  return -1
}

// 状态机：LOADING 清 error → OK 写入数据 → ERROR 留旧数据 + 写 error → TICK 仅更新时间戳
function reducer(s: DashboardState, a: DashboardAction): DashboardState {
  switch (a.type) {
    case 'LOADING': return { ...s, loading: true, error: null }
    case 'OK': return { ...s, loading: false, error: null, status: a.status, trades: a.trades, equity: a.equity, lastUpdated: Date.now() }
    case 'ERROR': return { ...s, loading: false, error: a.error }
    case 'TICK': return { ...s, lastUpdated: Date.now() }
    // Agent 实时日志：agent_input 时清空上轮，tool_call end 配对 start，保留最新 100 条
    case 'AGENT_EVENT': {
      let base = s.agentEvents
      if (a.event.type === 'agent_input') base = []

      // tool_call end：找到同 agent 同 tool 的 start 事件，补全 result
      if (a.event.type === 'agent_tool_call' && !a.event.args && a.event.result) {
        const idx = findLastIndex(base, e =>
          e.type === 'agent_tool_call' && e.agent === a.event.agent && e.tool === a.event.tool && !e.result
        )
        if (idx >= 0) {
          const merged = [...base]
          merged[idx] = { ...merged[idx], result: a.event.result, ts: a.event.ts }
          if (merged.length > 100) merged.splice(0, merged.length - 100)
          return { ...s, agentEvents: merged }
        }
      }

      const next = [...base, a.event]
      if (next.length > 100) next.splice(0, next.length - 100)
      return { ...s, agentEvents: next }
    }
    // Agent 历史日志（从 API 加载）
    case 'AGENT_LOGS': return { ...s, agentLogs: a.logs }
  }
}

const Ctx = createContext<{ state: DashboardState; refresh: () => void; wsConnected: boolean } | null>(null)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, init)
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  // 并行请求三个接口，任一一失败整个状态标记为 error
  const refresh = useCallback(async () => {
    dispatch({ type: 'LOADING' })
    try {
      const [status, trades, equity] = await Promise.all([
        fetchStatus(),
        fetchTrades(20),
        fetchEquity(500),
      ])
      dispatch({ type: 'OK', status, trades, equity })
    } catch (err: unknown) {
      dispatch({ type: 'ERROR', error: err instanceof Error ? err.message : '请求失败' })
    }
  }, [])

  // 首屏立即加载一次
  useEffect(() => { refresh() }, [refresh])

  // 加载 Agent 历史日志（Redis 持久化，刷新页面后恢复）
  useEffect(() => {
    fetchAgentLogs(5).then(logs => dispatch({ type: 'AGENT_LOGS', logs })).catch(() => {})
  }, [])

  // 定时轮询：每 5 秒全量刷新
  useEffect(() => {
    timerRef.current = setInterval(refresh, 5000)
    return () => clearInterval(timerRef.current)
  }, [refresh])

  // WebSocket 连接状态
  const [wsConnected, setWsConnected] = useState(false)

  // WebSocket 监听 tick_complete 事件，收到后增量刷新（先更新时间戳，再拉数据）
  useEffect(() => {
    const ws = connectWs((event) => {
      if (event.type === 'tick_complete') {
        setWsConnected(true)
        dispatch({ type: 'TICK' })
        refresh()
      } else if (event.type === 'circuit_breaker' && event.reason === 'ws_disconnected') {
        setWsConnected(false)
      } else if (event.type === 'agent_input' || event.type === 'agent_output' || event.type === 'agent_tool_call') {
        dispatch({ type: 'AGENT_EVENT', event: event as AgentEvent })
      }
    })
    // 连接建立后标记
    const timer = setTimeout(() => setWsConnected(true), 500)
    return () => { ws.close(); clearTimeout(timer) }
  }, [refresh])

  return <Ctx.Provider value={{ state, refresh, wsConnected }}>{children}</Ctx.Provider>
}

export function useDashboard() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useDashboard need DashboardProvider')
  return ctx
}
