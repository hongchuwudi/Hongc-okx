/**
 * 创建时间: 2026-06-07
 * 作者: hongchuwudi
 * 文件名: AgentOffice.tsx AI 智能体状态面板
 * 描述: 5 Agent 实时状态面板，通过 /api/agents/status 获取真实数据
 *
 * 包含:
 * - 类型: AgentState — 单个 Agent 的前端展示状态
 * - 组件: AgentOffice — 5 Agent 实时状态面板
 * - 常量: AGENTS — 5 Agent 的 ID/名称/角色/颜色定义
 * - 函数: mapState — 将后端事件映射为前端状态
 */
import { useState, useEffect, useRef } from 'react'
import TradingFloor from '../trading/TradingFloor'
import type { AgentEvent, AgentStatusResponse } from '../../types/dashboard'

// 单个 Agent 的前端展示状态
interface AgentState {
  id: string
  name: string
  role: string
  accent: string
  state: 'idle' | 'working' | 'done'
  text: string
  handoff: string
  toolCount: number
}

// 5 Agent 定义 — ID、中文名、角色描述、主题色
const AGENTS = [
  { id: 'scheduler', name: '调度师', role: '扫描市场状态，分配分析任务', accent: '#f59e0b' },
  { id: 'analyst', name: '分析师', role: '技术指标分析，识别交易信号', accent: '#ffd66e' },
  { id: 'reviewer', name: '复盘师', role: '回顾历史决策，总结经验教训', accent: '#6ee7ff' },
  { id: 'risk', name: '风控官', role: '评估风险敞口，设定仓位上限', accent: '#ff6e6e' },
  { id: 'trader', name: '交易员', role: '综合团队意见，下达最终指令', accent: '#a7ff83' },
]

// 握手目标映射
const HANDOFF_NAMES: Record<string, string> = {
  analyst: '分析师', reviewer: '复盘师', risk: '风控官', trader: '交易员',
  scheduler: '调度师', none: '', '': '',
}

// 将后端事件类型映射为前端状态
function agentState(event: AgentEvent | null): 'idle' | 'working' | 'done' {
  if (!event) return 'idle'
  if (event.type === 'agent_output') return 'done'
  return 'working'
}

// 提取事件的展示文本
function eventText(event: AgentEvent | null): string {
  if (!event) return ''
  if (event.type === 'agent_output') return event.output || ''
  if (event.type === 'agent_tool_call') return `调用 ${event.tool || ''}: ${(event.result || '').slice(0, 60)}`
  if (event.type === 'agent_input') return event.input || ''
  return ''
}

export default function AgentOffice({ aiReason, lastUpdate }: { aiReason: string; lastUpdate: number | null }) {
  const [agents, setAgents] = useState<AgentState[]>(
    AGENTS.map(a => ({ ...a, state: 'idle' as const, text: '', handoff: '', toolCount: 0 }))
  )
  const timerRef = useRef<ReturnType<typeof setInterval>>()

  // 每 2 秒拉取 Agent 状态
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('/api/v1/agents/status')
        if (!res.ok) return
        const data: AgentStatusResponse = await res.json()

        setAgents(prev => prev.map(a => {
          const entry = data.agents[a.id]
          if (!entry?.latest) return { ...a, state: 'idle' as const, text: '', handoff: '', toolCount: 0 }

          const latest = entry.latest
          // 统计本 Agent 最近的 tool_call 次数
          const toolCount = data.history.filter(
            e => e.agent === a.id && e.type === 'agent_tool_call'
          ).length

          return {
            ...a,
            state: agentState(latest),
            text: eventText(latest),
            handoff: latest.handoff ? HANDOFF_NAMES[latest.handoff] || latest.handoff : '',
            toolCount,
          }
        }))
      } catch { /* 后端未启动时静默 */ }
    }

    poll() // 立即执行一次
    timerRef.current = setInterval(poll, 2000)
    return () => clearInterval(timerRef.current)
  }, [])

  // 超时回 idle
  useEffect(() => {
    const t = setInterval(() => {
      if (lastUpdate && Date.now() - lastUpdate > 120000) {
        setAgents(prev => prev.map(a => ({ ...a, state: 'idle' as const, text: '', handoff: '', toolCount: 0 })))
      }
    }, 10000)
    return () => clearInterval(t)
  }, [lastUpdate])

  // 状态标签和颜色
  const stateLabel: Record<string, string> = { idle: '空闲', working: '工作中', done: '已完成' }
  const stateColor: Record<string, string> = { idle: 'var(--color-base-content)', working: '#f59e0b', done: '#a7ff83' }

  return (
    <div className="agent-layout" style={{ gap: 6, height: '100%', minHeight: 360 }}>
      <TradingFloor aiReason={aiReason} lastUpdate={lastUpdate} />

      <style>{`
        .agent-layout { display: flex; flex-direction: column; }
        @media (min-width: 768px) { .agent-layout { display: grid; grid-template-columns: 3fr 2fr; } }
      `}</style>

      {/* 5 Agent 卡片 — 第一行 3 个 第二行 2 个 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gridTemplateRows: '1fr 1fr',
        gap: 5, height: '100%',
      }}>
        {/* 调度师单独占第一行第一个（或让前3个占第一行） */}
        {agents.slice(0, 3).map(a => (
          <AgentCard key={a.id} agent={a} stateLabel={stateLabel} stateColor={stateColor} />
        ))}
        {/* 第二行：风控 + 交易员 */}
        <div style={{ display: 'contents' }}>
          {agents.slice(3, 5).map(a => (
            <AgentCard key={a.id} agent={a} stateLabel={stateLabel} stateColor={stateColor} />
          ))}
          {/* 占位格：让 5 个卡片在 3 列网格中美观排列 */}
          <div />
        </div>
      </div>
    </div>
  )
}

// 单个 Agent 卡片
function AgentCard({ agent: a, stateLabel, stateColor }: {
  agent: AgentState
  stateLabel: Record<string, string>
  stateColor: Record<string, string>
}) {
  return (
    <div style={{
      background: 'var(--color-base-100)',
      border: '1px solid var(--color-base-300)',
      borderRadius: 8, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 4,
      opacity: a.state === 'idle' ? 0.55 : 1,
      transition: 'opacity .3s',
    }}>
      {/* 顶行: 圆点 + 名字 + 状态 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <div style={{
          width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
          background: a.accent,
          boxShadow: a.state !== 'idle' ? `0 0 5px ${a.accent}` : 'none',
          transition: 'box-shadow .3s',
        }} />
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-base-content)', lineHeight: 1.2 }}>
          {a.name}
        </span>
        {a.handoff && (
          <span style={{ fontSize: 9, color: 'var(--color-base-content)', opacity: 0.4, marginLeft: 'auto' }}>
            → {a.handoff}
          </span>
        )}
        <span style={{
          fontSize: 8, fontWeight: 500, padding: '1px 6px', borderRadius: 3,
          background: 'var(--color-base-200)',
          color: stateColor[a.state],
          marginLeft: a.handoff ? 0 : 'auto',
        }}>
          {stateLabel[a.state]}
        </span>
      </div>

      {/* 角色描述（空闲时） */}
      {a.state === 'idle' && (
        <div style={{ fontSize: 9, color: 'var(--color-base-content)', opacity: 0.3, lineHeight: 1.3 }}>
          {a.role}
        </div>
      )}

      {/* 输出内容 */}
      {a.text && a.state !== 'idle' && (
        <div style={{
          fontSize: 10, color: 'var(--color-base-content)', opacity: 0.6,
          lineHeight: 1.4, flex: 1,
          overflow: 'hidden', textOverflow: 'ellipsis',
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          maxHeight: 40,
        }}>
          {a.text.slice(0, 100)}
        </div>
      )}

      {/* 工具调用计数 */}
      {a.toolCount > 0 && a.state !== 'idle' && (
        <div style={{ fontSize: 8, color: 'var(--color-base-content)', opacity: 0.3 }}>
          {a.toolCount} 次工具调用
        </div>
      )}
    </div>
  )
}
