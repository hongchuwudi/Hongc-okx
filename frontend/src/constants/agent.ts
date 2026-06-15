/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: Agent 展示常量 — 名称映射、颜色、顺序
 *
 * 包含:
 * - AGENT_INFO — Agent 名称 → { label, color } 映射
 * - AGENT_ORDER — 显示顺序（从调度到交易）
 */

/** Agent 中文名和颜色映射 */
export const AGENT_INFO: Record<string, { label: string; color: string }> = {
  scheduler:      { label: '调度师',   color: '#3b82f6' },  // blue
  analyst:        { label: '分析师',   color: '#22c55e' },  // green
  reviewer:       { label: '复盘师',   color: '#a855f7' },  // purple
  risk:           { label: '风控师',   color: '#f97316' },  // orange
  trader:         { label: '交易员',   color: '#ef4444' },  // red
  solo:           { label: 'Solo',     color: '#06b6d4' },  // cyan
  super_analyst:  { label: '超级分析', color: '#8b5cf6' },  // violet
}

/** Agent 在 5 Agent 模式下的执行顺序 */
export const AGENT_ORDER_5 = ['scheduler', 'analyst', 'reviewer', 'risk', 'trader']

/** Agent 在 3 Agent 模式下的执行顺序 */
export const AGENT_ORDER_3 = ['super_analyst', 'risk', 'trader']

/** Agent 在 Solo 模式下的执行顺序 */
export const AGENT_ORDER_SOLO = ['solo']

/** 模式名称映射 */
export const MODE_LABEL: Record<string, string> = {
  '5_agent': '5 Agent Swarm',
  '3_agent': '3 Agent 快速',
  '1_agent': '1 Agent 急速',
  tech: '纯技术指标',
}

/**
 * 根据 agent_mode 返回对应的 Agent 顺序列表。
 * tech 模式返回空数组（不使用 Agent）。
 */
export function getAgentOrder(mode: string): string[] {
  if (mode === '1_agent') return AGENT_ORDER_SOLO
  if (mode === '3_agent') return AGENT_ORDER_3
  if (mode === 'tech') return []
  return AGENT_ORDER_5
}
