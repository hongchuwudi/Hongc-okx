/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: WebSocket 事件类型
 */

import type { Position } from './dashboard'

// 引擎每 tick 推送 (type=tick_complete)
export interface WsTickEvent {
  type: 'tick_complete'
  timestamp: string
  btc_price: number
  equity: number
  signal: string
  confidence: string
  reason: string
  position: Position | null
}

// 熔断事件 (type=circuit_breaker)
export interface WsCircuitBreakEvent {
  type: 'circuit_breaker'
  reason: string
  state?: 'paused' | 'stopped'
}

// 回测完成事件
export interface WsBacktestDoneEvent {
  type: 'backtest_done'
  run_id: number
  metrics: Record<string, number> | null
  trades_count: number
}

// 回测错误事件
export interface WsBacktestErrorEvent {
  type: 'backtest_error'
  run_id: number
  error: string
}

// Agent 实时日志 (type=agent_input / agent_output)
export interface WsAgentEvent {
  type: 'agent_input' | 'agent_output'
  agent: string
  ts: string
  input?: string
  output?: string
  handoff?: string
}

// Agent 工具调用日志 (type=agent_tool_call)
export interface WsAgentToolCallEvent {
  type: 'agent_tool_call'
  agent: string
  ts: string
  tool: string
  args: string
  result: string
}

export type WsEvent = WsTickEvent | WsCircuitBreakEvent | WsBacktestDoneEvent | WsBacktestErrorEvent | WsAgentEvent | WsAgentToolCallEvent
