/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 运行时配置侧边栏常量 — 字段标签、选项、提示
 */

import type { ReactNode } from 'react'

// 字段元信息
export interface ConfigFieldMeta {
  key: string
  label: string
  type: 'select' | 'number'
  options?: { label: string; value: string }[]
  step?: number
  min?: number
  max?: number
  hint?: string
  instant: boolean  // true=即时生效，false=重启后生效
}

// 执行方案选项
export const AGENT_MODE_OPTIONS = [
  { label: '技术指标 (纯规则)', value: 'tech' },
  { label: '1 Agent 急速', value: '1_agent' },
  { label: '3 Agent 快速', value: '3_agent' },
  { label: '5 Agent 完整', value: '5_agent' },
]

// 交易对选项
export const SYMBOL_OPTIONS = [
  { label: 'DOGE/USDT:USDT', value: 'DOGE/USDT:USDT' },
  { label: 'BTC/USDT:USDT', value: 'BTC/USDT:USDT' },
  { label: 'ETH/USDT:USDT', value: 'ETH/USDT:USDT' },
]

// K 线周期选项
export const TIMEFRAME_OPTIONS = [
  { label: '1 分钟', value: '1m' },
  { label: '3 分钟', value: '3m' },
  { label: '5 分钟', value: '5m' },
  { label: '15 分钟', value: '15m' },
  { label: '1 小时', value: '1h' },
  { label: '4 小时', value: '4h' },
]

// Tick 间隔选项
export const TICK_INTERVAL_OPTIONS = [
  { label: '2 分钟', value: '120' },
  { label: '3 分钟', value: '180' },
  { label: '5 分钟', value: '300' },
  { label: '6 分钟', value: '360' },
  { label: '10 分钟', value: '600' },
  { label: '15 分钟', value: '900' },
]

// 杠杆选项
export const LEVERAGE_OPTIONS = [
  { label: '3x', value: '3' },
  { label: '5x', value: '5' },
  { label: '10x', value: '10' },
  { label: '20x', value: '20' },
]

// 所有运行时配置字段定义
export const CONFIG_FIELDS: ConfigFieldMeta[] = [
  // ── 交易参数 ──
  { key: 'agent_mode', label: '执行方案', type: 'select', options: AGENT_MODE_OPTIONS, instant: true, hint: '重启后生效' },
  { key: 'symbol', label: '交易对', type: 'select', options: SYMBOL_OPTIONS, instant: true, hint: '重启后生效' },
  { key: 'timeframe', label: 'K 线周期', type: 'select', options: TIMEFRAME_OPTIONS, instant: true, hint: '重启后生效' },
  { key: 'tick_interval_seconds', label: 'Tick 间隔', type: 'select', options: TICK_INTERVAL_OPTIONS, instant: true, hint: '重启后生效' },
  { key: 'leverage', label: '杠杆倍数', type: 'select', options: LEVERAGE_OPTIONS, instant: true, hint: '重启后生效' },
  { key: 'order_amount', label: '下单金额 (USDT)', type: 'number', step: 0.5, min: 0.5, max: 1000, instant: true },
  // ── 风控参数 ──
  { key: 'max_position_ratio', label: '最大仓位比例', type: 'number', step: 0.05, min: 0.1, max: 1.0, instant: true },
  { key: 'max_daily_drawdown_pct', label: '最大日回撤 (%)', type: 'number', step: 1, min: 1, max: 50, instant: true },
  { key: 'max_daily_loss_usdt', label: '最大日亏损 (USDT)', type: 'number', step: 5, min: 5, max: 5000, instant: true },
  // ── 账户模式 ──
  { key: 'sandbox', label: '交易模式', type: 'select', options: [{ label: '模拟盘', value: 'true' }, { label: '实盘', value: 'false' }], instant: false, hint: '重启后生效' },
]
