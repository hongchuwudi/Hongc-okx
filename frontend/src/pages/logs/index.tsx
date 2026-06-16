/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: Agent 日志页面 — 左侧方案选择 + 顶部导航栏 + 分页日志流
 *
 * 包含:
 * - 左侧栏 — 方案选择（全部/5 Agent/3 Agent/1 Agent/技术指标）
 * - 顶部栏 — 当前方案名称 + 实时状态 + 搜索框 + 自动滚动
 * - 核心区 — 分页日志列表
 * - 底部分页 — 页码导航
 */

import { useMemo, useRef, useState, useEffect, useCallback } from 'react'
import { useDashboardStore } from '@/stores/dashboardStore'
import { AGENT_INFO, getAgentOrder, MODE_LABEL } from '@/constants/agent'
import MarkdownViewer from '@/components/common/MarkdownViewer'
import FormInput from '@/components/common/FormInput'
import type { AgentEvent } from '@/types/dashboard'

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

function stripEmoji(text: string): string {
  return text.replace(/[\p{Emoji_Presentation}\p{Emoji}]+/gu, '').replace(/\s*\n{3,}/g, '\n\n').trim()
}

// ---------------------------------------------------------------------------
// 方案列表
// ---------------------------------------------------------------------------

const MODE_LIST = [
  { key: 'all',     label: '全部 Agent',  order: [] as string[] },
  { key: '5_agent', label: '5 Agent Swarm', order: getAgentOrder('5_agent') },
  { key: '3_agent', label: '3 Agent 快速',  order: getAgentOrder('3_agent') },
  { key: '1_agent', label: '1 Agent 急速',  order: getAgentOrder('1_agent') },
  { key: 'tech',    label: '纯技术指标',    order: getAgentOrder('tech') },
]

// ---------------------------------------------------------------------------
// LogEntry
// ---------------------------------------------------------------------------

function LogEntry({ event, expandedTools, toggleTool, searchText }: {
  event: AgentEvent
  expandedTools: Set<string>
  toggleTool: (key: string) => void
  searchText: string
}) {
  const info = AGENT_INFO[event.agent] ?? { label: event.agent, color: '#9ca3af' }
  const toolKey = `${event.agent}-${event.tool}-${event.ts}`

  const highlight = (text: string) => {
    if (!searchText || !text) return text
    const idx = text.toLowerCase().indexOf(searchText.toLowerCase())
    if (idx < 0) return text
    return (
      <>
        {text.slice(0, idx)}
        <mark className="bg-amber-400/30 text-inherit rounded px-0.5">{text.slice(idx, idx + searchText.length)}</mark>
        {text.slice(idx + searchText.length)}
      </>
    )
  }

  // ── RECV ──
  if (event.type === 'agent_input') {
    return (
      <div className="group py-1 pl-4 border-l-2 border-base-300 hover:border-base-400 transition-colors">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-base-content/30 font-mono shrink-0 w-[80px]">{fmtMs(event.ts)}</span>
          <span className="text-[11px] font-medium px-1.5 py-0.5 rounded shrink-0"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}>
            {info.label}
          </span>
          <span className="text-[10px] text-base-content/30 font-medium tracking-wider">RECV</span>
        </div>
        {event.input && (
          <div className="text-xs text-base-content/50 mt-0.5 ml-[108px] font-mono leading-relaxed">
            {highlight(event.input)}
          </div>
        )}
      </div>
    )
  }

  // ── TOOL ──
  if (event.type === 'agent_tool_call') {
    const isExpanded = expandedTools.has(toolKey)
    const isComplete = !!event.result
    return (
      <div className="group py-1 pl-4 border-l-2 border-amber-500/30 hover:border-amber-500/60 transition-colors">
        <div className="flex items-center gap-2 cursor-pointer select-none"
          onClick={() => toggleTool(toolKey)}>
          <span className="text-[11px] text-base-content/30 font-mono shrink-0 w-[80px]">{fmtMs(event.ts)}</span>
          <span className="text-[11px] font-medium px-1.5 py-0.5 rounded shrink-0"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}>
            {info.label}
          </span>
          <span className="text-[11px] text-amber-500 font-medium font-mono">{event.tool}</span>
          {!isComplete && <span className="text-[10px] text-base-content/30 animate-pulse">running...</span>}
          <span className="text-[10px] text-base-content/30 transition-transform duration-200"
            style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}>
            ▶
          </span>
        </div>
        {isExpanded && (
          <div className="ml-[108px] mt-1 mb-1 font-mono text-xs bg-base-200 rounded p-2 space-y-1">
            {event.args && (
              <div className="flex gap-2">
                <span className="text-base-content/30 shrink-0">args:</span>
                <span className="text-base-content/70 break-all">{highlight(event.args)}</span>
              </div>
            )}
            {isComplete && (
              <div className="flex gap-2">
                <span className="text-base-content/30 shrink-0">result:</span>
                <span className="text-base-content/70 break-all whitespace-pre-wrap">{highlight(event.result ?? '')}</span>
              </div>
            )}
          </div>
        )}
        {!isExpanded && isComplete && event.result && (
          <div className="text-[11px] text-base-content/40 ml-[108px] truncate font-mono">
            {event.result.slice(0, 120)}
          </div>
        )}
      </div>
    )
  }

  // ── DONE ──
  if (event.type === 'agent_output') {
    const clean = stripEmoji(event.output ?? '')
    const handoffName = event.handoff && event.handoff !== 'none' ? event.handoff : null
    const handoffInfo = handoffName ? AGENT_INFO[handoffName] : null
    return (
      <div className="group py-1.5 pl-4 border-l-2 border-emerald-500/30 hover:border-emerald-500/60 transition-colors">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-base-content/30 font-mono shrink-0 w-[80px]">{fmtMs(event.ts)}</span>
          <span className="text-[11px] font-medium px-1.5 py-0.5 rounded shrink-0"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}>
            {info.label}
          </span>
          <span className="text-[10px] text-emerald-500 font-medium tracking-wider">DONE</span>
          {handoffInfo && (
            <>
              <span className="text-[10px] text-base-content/25">→</span>
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                style={{ backgroundColor: `${handoffInfo.color}20`, color: handoffInfo.color }}>
                {handoffInfo.label}
              </span>
            </>
          )}
        </div>
        {clean && (
          <div className="ml-[108px] mt-1 text-sm leading-relaxed">
            <MarkdownViewer content={clean} fontSize={13} />
          </div>
        )}
      </div>
    )
  }

  return null
}

// ---------------------------------------------------------------------------
// 分页控件
// ---------------------------------------------------------------------------

function Pagination({ page, totalPages, onPage }: {
  page: number
  totalPages: number
  onPage: (p: number) => void
}) {
  if (totalPages <= 1) return null

  const pages: number[] = []
  const start = Math.max(1, page - 2)
  const end = Math.min(totalPages, page + 2)
  for (let i = start; i <= end; i++) pages.push(i)

  return (
    <div className="flex items-center justify-center gap-1 py-2">
      <button
        onClick={() => onPage(page - 1)}
        disabled={page <= 1}
        className="btn btn-xs btn-ghost disabled:opacity-30"
      >
        上一页
      </button>
      {start > 1 && (
        <>
          <button onClick={() => onPage(1)} className="btn btn-xs btn-ghost">1</button>
          {start > 2 && <span className="text-base-content/20 text-xs">...</span>}
        </>
      )}
      {pages.map(p => (
        <button
          key={p}
          onClick={() => onPage(p)}
          className={`btn btn-xs ${p === page ? 'btn-primary' : 'btn-ghost'}`}
        >
          {p}
        </button>
      ))}
      {end < totalPages && (
        <>
          {end < totalPages - 1 && <span className="text-base-content/20 text-xs">...</span>}
          <button onClick={() => onPage(totalPages)} className="btn btn-xs btn-ghost">{totalPages}</button>
        </>
      )}
      <button
        onClick={() => onPage(page + 1)}
        disabled={page >= totalPages}
        className="btn btn-xs btn-ghost disabled:opacity-30"
      >
        下一页
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// LogsPage
// ---------------------------------------------------------------------------

export default function LogsPage() {
  const agentEvents = useDashboardStore(s => s.agentEvents)
  const status = useDashboardStore(s => s.status)
  const currentMode = status?.agent_mode ?? '5_agent'

  // 方案选择
  const [selectedMode, setSelectedMode] = useState('all')

  // 搜索 & 分页
  const PAGE_SIZE = 20
  const [searchText, setSearchText] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [autoScroll, setAutoScroll] = useState(true)

  // 折叠工具调用
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const toggleTool = useCallback((key: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }, [])

  // 过滤
  const filteredEvents = useMemo(() => {
    let events = agentEvents

    // 方案过滤
    if (selectedMode !== 'all') {
      const modeOrder = getAgentOrder(selectedMode)
      if (modeOrder.length > 0) {
        events = events.filter(e => modeOrder.includes(e.agent))
      } else {
        // tech 模式无 agent，显示空
        return []
      }
    }

    // 搜索
    if (searchText) {
      const q = searchText.toLowerCase()
      events = events.filter(e => {
        const haystack = [e.input, e.output, e.tool, e.args, e.result, e.agent].filter(Boolean).join(' ').toLowerCase()
        return haystack.includes(q)
      })
    }

    return events
  }, [agentEvents, selectedMode, searchText])

  // 分页
  const totalPages = Math.max(1, Math.ceil(filteredEvents.length / PAGE_SIZE))
  const safePage = Math.min(currentPage, totalPages)
  const paginatedEvents = useMemo(() => {
    const start = (safePage - 1) * PAGE_SIZE
    return filteredEvents.slice(start, start + PAGE_SIZE)
  }, [filteredEvents, safePage])

  // 新事件到来时，如果在最后一页则自动翻页
  const prevLenRef = useRef(agentEvents.length)
  useEffect(() => {
    if (autoScroll && agentEvents.length > prevLenRef.current && currentPage === totalPages) {
      // 新事件到达，保持在最新页
    }
    prevLenRef.current = agentEvents.length
  }, [agentEvents.length, autoScroll, currentPage, totalPages])

  // 过滤变化时回到第一页
  useEffect(() => {
    setCurrentPage(1)
  }, [selectedMode, searchText])

  // 自动滚动到底部（在最后一页时）
  const streamRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (autoScroll && safePage === totalPages && streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight
    }
  }, [paginatedEvents, autoScroll, safePage, totalPages])

  const hasEvents = agentEvents.length > 0
  const selectedLabel = MODE_LIST.find(m => m.key === selectedMode)?.label ?? '全部 Agent'

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* ================================================================ */}
      {/* 左侧栏 — 方案选择                                                */}
      {/* ================================================================ */}
      <div className="w-44 shrink-0 border-r border-base-300 bg-base-100 flex flex-col">
        <div className="px-3 py-3 text-xs text-base-content/40 font-medium tracking-wider">
          方案选择
        </div>
        <div className="flex-1 overflow-y-auto">
          {MODE_LIST.map(item => {
            const agentLen = item.order.length
            return (
              <button
                key={item.key}
                onClick={() => setSelectedMode(item.key)}
                className={`w-full text-left px-3 py-2 text-sm transition-colors flex items-center justify-between
                  ${selectedMode === item.key
                    ? 'bg-primary/10 text-primary font-medium border-r-2 border-primary'
                    : 'text-base-content/60 hover:bg-base-200 hover:text-base-content'
                  }`}
              >
                <span>{item.label}</span>
                {agentLen > 0 && (
                  <span className="text-[10px] text-base-content/25 font-mono">{agentLen} agents</span>
                )}
              </button>
            )
          })}
        </div>
        <div className="px-3 py-2 border-t border-base-200">
          <span className="text-[10px] text-base-content/30">
            当前: {MODE_LABEL[currentMode] ?? currentMode}
          </span>
        </div>
      </div>

      {/* ================================================================ */}
      {/* 右侧 — 日志主区                                                  */}
      {/* ================================================================ */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* ── 顶部导航栏 ───────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-2 bg-base-100 border-b border-base-300 shrink-0">
          <span className="text-sm font-medium">{selectedLabel}</span>
          {hasEvents && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-500 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              LIVE
            </span>
          )}
          <span className="text-[10px] text-base-content/30 font-mono ml-auto">
            共 {filteredEvents.length} 条
          </span>

          <FormInput
            type="text"
            size="xs"
            placeholder="搜索..."
            value={searchText}
            onChange={setSearchText}
            className="w-40 bg-base-200 text-xs border-0"
          />

          <FormInput
            type="checkbox"
            size="xs"
            checked={autoScroll}
            onChange={setAutoScroll}
            label="自动滚动"
          />
        </div>

        {/* ── 日志列表 ──────────────────────────────────────────────── */}
        <div ref={streamRef} className="flex-1 overflow-y-auto">
          {filteredEvents.length === 0 && (
            <div className="text-center text-sm text-base-content/25 pt-20 select-none">
              {hasEvents ? '无匹配事件' : '等待中...'}
            </div>
          )}

          {paginatedEvents.map((event, i) => (
            <LogEntry
              key={`${event.agent}-${event.type}-${event.ts}-${i}`}
              event={event}
              expandedTools={expandedTools}
              toggleTool={toggleTool}
              searchText={searchText}
            />
          ))}

          <div className="h-4" />
        </div>

        {/* ── 底部分页 ──────────────────────────────────────────────── */}
        <div className="shrink-0 border-t border-base-200 bg-base-100 px-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-base-content/30">
              第 {safePage}/{totalPages} 页
            </span>
            <Pagination page={safePage} totalPages={totalPages} onPage={setCurrentPage} />
            <span className="text-[10px] text-base-content/30">
              {PAGE_SIZE} 条/页
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
