/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 仪表盘状态 store — zustand 实现，HTTP 轮询 + WebSocket 推送 + Agent 事件
 */

import { create } from 'zustand'
import type { DashboardState, AgentEvent } from '@/types/dashboard'
import { fetchStatus, fetchEquity, fetchAgentLogs } from '@/api/dashboard'
import { fetchTrades } from '@/api/trades'
import { connectWs } from '@/utils/ws'

interface DashboardStore extends DashboardState {
  wsConnected: boolean
  init: () => void
  destroy: () => void
  refresh: () => Promise<void>
  _addAgentEvent: (event: AgentEvent) => void
}

function findLastIndex<T>(arr: T[], predicate: (item: T) => boolean): number {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (predicate(arr[i])) return i
  }
  return -1
}

let _timer: ReturnType<typeof setInterval> | null = null
let _ws: { close: () => void } | null = null
let _wsTimer: ReturnType<typeof setTimeout> | null = null
let _initialized = false

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  // 初始状态
  status: null,
  trades: [],
  equity: [],
  loading: true,
  error: null,
  lastUpdated: null,
  agentEvents: [],
  agentLogs: [],
  wsConnected: false,

  // 启动轮询 + WebSocket
  init: () => {
    if (_initialized) return
    _initialized = true

    const { refresh } = get()

    // 首屏加载
    refresh()

    // Agent 历史日志
    fetchAgentLogs(5).then(logs => set({ agentLogs: logs })).catch(() => {})

    // 5s 轮询
    _timer = setInterval(refresh, 5000)

    // WebSocket
    _ws = connectWs((event) => {
      if (event.type === 'tick_complete') {
        set({ wsConnected: true })
        refresh()
      } else if (event.type === 'circuit_breaker' && event.reason === 'ws_disconnected') {
        set({ wsConnected: false })
      } else if (event.type === 'agent_input' || event.type === 'agent_output' || event.type === 'agent_tool_call') {
        get()._addAgentEvent(event as AgentEvent)
      }
    })
    _wsTimer = setTimeout(() => set({ wsConnected: true }), 500)
  },

  // 清理
  destroy: () => {
    _initialized = false
    if (_timer) { clearInterval(_timer); _timer = null }
    if (_ws) { _ws.close(); _ws = null }
    if (_wsTimer) { clearTimeout(_wsTimer); _wsTimer = null }
  },

  // 刷新数据
  refresh: async () => {
    set({ loading: true, error: null })
    try {
      const [status, trades, equity] = await Promise.all([
        fetchStatus(), fetchTrades(20), fetchEquity(500),
      ])
      set({ loading: false, status, trades, equity, lastUpdated: Date.now() })
    } catch (err: unknown) {
      set({ loading: false, error: err instanceof Error ? err.message : '请求失败' })
    }
  },

  // Agent 事件处理
  _addAgentEvent: (event: AgentEvent) => {
    const { agentEvents } = get()
    let base = agentEvents
    if (event.type === 'agent_input') base = []

    // tool_call end 配对 start
    if (event.type === 'agent_tool_call' && !event.args && event.result) {
      const idx = findLastIndex(base, e =>
        e.type === 'agent_tool_call' && e.agent === event.agent && e.tool === event.tool && !e.result
      )
      if (idx >= 0) {
        const merged = [...base]
        merged[idx] = { ...merged[idx], result: event.result, ts: event.ts }
        if (merged.length > 100) merged.splice(0, merged.length - 100)
        set({ agentEvents: merged })
        return
      }
    }

    const next = [...base, event]
    if (next.length > 100) next.splice(0, next.length - 100)
    set({ agentEvents: next })
  },
}))
