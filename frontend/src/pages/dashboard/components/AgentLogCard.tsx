/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: Agent 实时日志卡片 — 管道流程可视化 + 实时日志流 + 工具调用展开 + 历史轮次
 *
 * 包含:
 * - PipelineBar — Agent 管道流程状态条
 * - LogStream — 实时日志流（输入/工具调用/输出三种条目）
 * - HistorySection — 历史轮次折叠面板
 */

import { useMemo, useRef, useState, useEffect, useCallback } from 'react'
import { useDashboardStore } from '@/stores/dashboardStore'
import { AGENT_INFO, getAgentOrder, MODE_LABEL } from '@/constants/agent'
import MarkdownViewer from '@/components/common/MarkdownViewer'
import type { AgentEvent, AgentTickLog } from '@/types/dashboard'
import type { AgentRunState } from '@/types/agents'

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function fmtMs(ts: string): string {
  const d = new Date(ts.includes('Z') || ts.includes('+') ? ts : ts + 'Z')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  const ms = String(d.getMilliseconds()).padStart(3, '0')
  return `${h}:${m}:${s}.${ms}`
}

function fmtShort(ts: string): string {
  const d = new Date(ts.includes('Z') || ts.includes('+') ? ts : ts + 'Z')
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

function stripEmoji(text: string): string {
  return text.replace(/[\p{Emoji_Presentation}\p{Emoji}‍]+/gu, '').replace(/\s*\n{3,}/g, '\n\n').trim()
}

// ---------------------------------------------------------------------------
// Agent 状态计算
// ---------------------------------------------------------------------------

function computeAgentStates(events: AgentEvent[], order: string[]): Record<string, AgentRunState> {
  const map: Record<string, AgentRunState> = {}
  for (const name of order) {
    map[name] = { hasInput: false, hasOutput: false, toolCount: 0, lastTs: null }
  }
  for (const e of events) {
    const s = map[e.agent]
    if (!s) continue
    s.lastTs = e.ts
    if (e.type === 'agent_input') s.hasInput = true
    if (e.type === 'agent_output') s.hasOutput = true
    if (e.type === 'agent_tool_call') s.toolCount++
  }
  return map
}

// ---------------------------------------------------------------------------
// PipelineBar — Agent 管道流程状态条
// ---------------------------------------------------------------------------

function PipelineBar({
  order,
  agentStates,
  agentEvents,
}: {
  order: string[]
  agentStates: Record<string, AgentRunState>
  agentEvents: AgentEvent[]
}) {
  const hasLive = agentEvents.length > 0
  return (
    <div className="flex items-center gap-1 px-1 py-1.5 overflow-x-auto">
      {order.map((name, i) => {
        const info = AGENT_INFO[name] ?? { label: name, color: '#9ca3af' }
        const s = agentStates[name]
        let status: 'idle' | 'active' | 'done' = 'idle'
        if (s?.hasOutput) status = 'done'
        else if (s?.hasInput) status = 'active'

        return (
          <div key={name} className="flex items-center gap-1 shrink-0">
            {i > 0 && <span className="text-[10px] text-base-content/20 mx-0.5">→</span>}
            <div className="flex items-center gap-1">
              {/* 状态指示点 */}
              <span
                className="block w-2 h-2 rounded-full shrink-0"
                style={{
                  backgroundColor: status === 'idle' ? 'transparent' : info.color,
                  border: status === 'idle' ? `1.5px solid ${info.color}40` : 'none',
                  boxShadow: status === 'active' ? `0 0 6px ${info.color}` : 'none',
                  transition: 'all 0.3s ease',
                }}
              />
              <span
                className="text-[11px] font-medium whitespace-nowrap"
                style={{
                  color: hasLive ? info.color : `${info.color}80`,
                  transition: 'color 0.3s ease',
                }}
              >
                {info.label}
              </span>
              {s?.toolCount > 0 && (
                <span className="text-[9px] text-base-content/40 font-mono">
                  {s.toolCount}
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// LogEntry — 单条日志条目
// ---------------------------------------------------------------------------

function LogEntry({
  event,
  expandedTools,
  toggleTool,
}: {
  event: AgentEvent
  expandedTools: Set<string>
  toggleTool: (key: string) => void
}) {
  const info = AGENT_INFO[event.agent] ?? { label: event.agent, color: '#9ca3af' }
  const toolKey = `${event.agent}-${event.tool}-${event.ts}`

  if (event.type === 'agent_input') {
    return (
      <div className="group py-0.5 pl-2 border-l-2 border-base-300 hover:border-base-400 transition-colors">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-base-content/30 font-mono shrink-0 w-[68px]">
            {fmtMs(event.ts)}
          </span>
          <span
            className="text-[10px] font-medium px-1 py-0 rounded shrink-0"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}
          >
            {info.label}
          </span>
          <span className="text-[10px] text-base-content/40 font-medium">RECV</span>
        </div>
        {event.input && (
          <div className="text-[11px] text-base-content/50 mt-0.5 ml-[84px] font-mono leading-relaxed line-clamp-3">
            {event.input}
          </div>
        )}
      </div>
    )
  }

  if (event.type === 'agent_tool_call') {
    const isExpanded = expandedTools.has(toolKey)
    const isComplete = !!event.result
    return (
      <div className="group py-0.5 pl-2 border-l-2 border-amber-500/40 hover:border-amber-500/70 transition-colors">
        <div
          className="flex items-center gap-1.5 cursor-pointer select-none"
          onClick={() => toggleTool(toolKey)}
        >
          <span className="text-[10px] text-base-content/30 font-mono shrink-0 w-[68px]">
            {fmtMs(event.ts)}
          </span>
          <span
            className="text-[10px] font-medium px-1 py-0 rounded shrink-0"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}
          >
            {info.label}
          </span>
          <span className="text-[10px] text-amber-500 font-medium font-mono">
            {event.tool}
          </span>
          {!isComplete && (
            <span className="text-[10px] text-base-content/30 animate-pulse">...</span>
          )}
          <span
            className="text-[10px] text-base-content/30 transition-transform duration-200"
            style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
          >
            ▶
          </span>
        </div>
        {/* 展开详情 */}
        {isExpanded && (
          <div className="ml-[84px] mt-0.5 mb-1 font-mono text-[11px]">
            {event.args && (
              <div className="flex gap-1">
                <span className="text-base-content/30 shrink-0">args:</span>
                <span className="text-base-content/60 break-all">{event.args}</span>
              </div>
            )}
            {isComplete && (
              <div className="flex gap-1">
                <span className="text-base-content/30 shrink-0">result:</span>
                <span className="text-base-content/70 break-all whitespace-pre-wrap">{event.result}</span>
              </div>
            )}
          </div>
        )}
        {/* 折叠态显示结果摘要 */}
        {!isExpanded && isComplete && event.result && (
          <div className="text-[10px] text-base-content/40 ml-[84px] truncate font-mono">
            {event.result.slice(0, 80)}
          </div>
        )}
      </div>
    )
  }

  // agent_output
  if (event.type === 'agent_output') {
    const clean = stripEmoji(event.output ?? '')
    const handoffName = event.handoff && event.handoff !== 'none' ? event.handoff : null
    const handoffInfo = handoffName ? AGENT_INFO[handoffName] : null
    return (
      <div className="group py-1 pl-2 border-l-2 border-emerald-500/40 hover:border-emerald-500/70 transition-colors">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-base-content/30 font-mono shrink-0 w-[68px]">
            {fmtMs(event.ts)}
          </span>
          <span
            className="text-[10px] font-medium px-1 py-0 rounded shrink-0"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}
          >
            {info.label}
          </span>
          <span className="text-[10px] text-emerald-500 font-medium">DONE</span>
          {handoffInfo && (
            <>
              <span className="text-[10px] text-base-content/30">→</span>
              <span
                className="text-[10px] font-medium px-1 py-0 rounded"
                style={{ backgroundColor: `${handoffInfo.color}20`, color: handoffInfo.color }}
              >
                {handoffInfo.label}
              </span>
            </>
          )}
        </div>
        {clean && (
          <div className="ml-[84px] mt-1 text-xs leading-relaxed">
            <MarkdownViewer content={clean} fontSize={12} />
          </div>
        )}
      </div>
    )
  }

  return null
}

// ---------------------------------------------------------------------------
// HistoryTick — 单条历史轮次
// ---------------------------------------------------------------------------

function HistoryTick({ log, order }: { log: AgentTickLog; order: string[] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-base-200 last:border-0">
      <div
        className="flex items-center gap-1.5 py-1 px-1 cursor-pointer hover:bg-base-200/50 rounded transition-colors select-none"
        onClick={() => setOpen(!open)}
      >
        <span
          className="text-[10px] text-base-content/30 transition-transform duration-200"
          style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }}
        >
          ▶
        </span>
        <span className="text-[10px] text-base-content/40 font-mono">{fmtShort(log.ts)}</span>
        <span className="text-[10px] text-base-content/30">{MODE_LABEL[log.mode] ?? log.mode}</span>
        {/* 各 Agent 状态小点 */}
        <span className="flex gap-0.5 ml-auto">
          {order.map((name) => {
            const info = AGENT_INFO[name] ?? { label: name, color: '#9ca3af' }
            const has = !!log.agents[name]
            return (
              <span
                key={name}
                className="block w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: has ? info.color : `${info.color}30` }}
                title={`${info.label}${has ? '' : ' (无)'}`}
              />
            )
          })}
        </span>
      </div>
      {open && (
        <div className="pb-1.5 space-y-1">
          {order.map((name) => {
            const data = log.agents[name]
            if (!data) return null
            const info = AGENT_INFO[name] ?? { label: name, color: '#9ca3af' }
            const clean = stripEmoji(data.output)
            return (
              <div key={name} className="pl-4">
                <span
                  className="text-[10px] font-medium px-1 py-0 rounded"
                  style={{ backgroundColor: `${info.color}20`, color: info.color }}
                >
                  {info.label}
                </span>
                {data.handoff && data.handoff !== 'none' && (
                  <span className="text-[10px] text-base-content/30 ml-1">→ {data.handoff}</span>
                )}
                <div className="mt-0.5 text-[11px] leading-relaxed">
                  <MarkdownViewer content={clean} fontSize={11} />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// AgentLogCard — 主组件
// ---------------------------------------------------------------------------

export default function AgentLogCard() {
  const agentEvents = useDashboardStore(s => s.agentEvents)
  const agentLogs = useDashboardStore(s => s.agentLogs)
  const status = useDashboardStore(s => s.status)
  const mode = status?.agent_mode ?? '5_agent'
  const modeLabel = MODE_LABEL[mode] ?? mode
  const order = getAgentOrder(mode)

  // 折叠的工具调用详情
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const toggleTool = useCallback((key: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev)
      if (next.has(key)) { next.delete(key) } else { next.add(key) }
      return next
    })
  }, [])

  // 智能自动滚动
  const streamRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [showScrollBtn, setShowScrollBtn] = useState(false)

  const scrollToBottom = useCallback(() => {
    const el = streamRef.current
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      setAutoScroll(true)
      setShowScrollBtn(false)
    }
  }, [])

  // 新事件到达时自动滚动
  useEffect(() => {
    if (autoScroll && streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight
    }
    if (!autoScroll && agentEvents.length > 0) {
      setShowScrollBtn(true)
    }
  }, [agentEvents, autoScroll])

  // 监听用户手动滚动
  const handleScroll = useCallback(() => {
    const el = streamRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    setAutoScroll(atBottom)
    if (atBottom) setShowScrollBtn(false)
  }, [])

  // Agent 运行状态
  const agentStates = useMemo(
    () => computeAgentStates(agentEvents, order),
    [agentEvents, order],
  )

  const hasLive = agentEvents.length > 0

  // 技术指标模式
  if (order.length === 0) {
    return (
      <div className="card bg-base-100 border border-base-300">
        <div className="card-body p-3 text-center text-sm text-base-content/40">
          技术指标模式，无 Agent 活动
        </div>
      </div>
    )
  }

  return (
    <div className="card bg-base-100 border border-base-300">
      <div className="card-body p-0">
        {/* 头部 */}
        <div className="flex items-center justify-between px-3 pt-2 pb-0">
          <span className="text-sm font-medium">Agent 实时日志</span>
          <div className="flex items-center gap-1.5">
            <span className="badge badge-xs badge-outline text-[10px]">{modeLabel}</span>
            {hasLive && (
              <span className="text-[9px] text-emerald-500 font-mono animate-pulse tracking-wider">
                LIVE
              </span>
            )}
          </div>
        </div>

        {/* 管道流程条 */}
        <PipelineBar order={order} agentStates={agentStates} agentEvents={agentEvents} />

        {/* 日志流 */}
        <div
          ref={streamRef}
          onScroll={handleScroll}
          className="relative flex flex-col max-h-[320px] overflow-y-auto border-t border-base-200"
          style={{ scrollBehavior: autoScroll ? 'auto' : undefined }}
        >
          {!hasLive && (
            <div className="text-center text-xs text-base-content/30 py-6 select-none">
              等待下一轮 Tick...
            </div>
          )}

          {agentEvents.map((event, i) => (
            <LogEntry
              key={`${event.agent}-${event.type}-${event.ts}-${i}`}
              event={event}
              expandedTools={expandedTools}
              toggleTool={toggleTool}
            />
          ))}

          {/* 滚动到底部按钮 */}
          {showScrollBtn && (
            <button
              onClick={scrollToBottom}
              className="sticky bottom-2 mx-auto btn btn-primary btn-xs rounded-full shadow-lg z-10"
            >
              回到底部
            </button>
          )}
        </div>

        {/* 历史轮次 */}
        {agentLogs.length > 0 && (
          <div className="border-t border-base-300">
            <div className="flex items-center gap-2 px-3 py-1.5">
              <span className="text-[10px] text-base-content/40 font-medium">
                历史轮次 ({agentLogs.length})
              </span>
            </div>
            <div className="max-h-[200px] overflow-y-auto px-2 pb-1">
              {agentLogs.map((log, i) => (
                <HistoryTick key={log.ts + i} log={log} order={order} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
