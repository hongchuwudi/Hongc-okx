/**
 * 创建时间: 2026-06-17
 * 作者: hongchuwudi
 * 描述: Agent 监控与配置页面 — 左侧方案选择 + 右侧日志/提示词双标签
 *
 * 包含:
 * - 组件: AgentsPage — 合并原 /logs 和 /prompts，共享侧边栏
 * - 标签: 决策日志（实时流 + 搜索 + 分页）/ 提示词（Agent 列表 + 编辑器）
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useDashboardStore } from '@/stores/dashboardStore'
import { AGENT_INFO, getAgentOrder, MODE_LABEL } from '@/constants/agent'
import { fetchPrompts, updatePrompt, resetPrompt, reloadAgents } from '@/api/agents'
import MarkdownViewer from '@/components/common/MarkdownViewer'
import FormInput from '@/components/common/FormInput'
import Paginator from '@/components/common/Paginator'
import PromptEditor from '@/components/PromptEditor'
import type { AgentEvent } from '@/types/dashboard'
import type { AgentPrompt } from '@/types/agents'
import { Search } from 'lucide-react'

// ---------------------------------------------------------------------------
// 工具
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

function highlightText(text: string, query: string) {
  if (!query || !text) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx < 0) return text
  return (
    <>
      {text.slice(0, idx)}
      <mark className="bg-amber-400/30 text-inherit rounded px-0.5">{text.slice(idx, idx + query.length)}</mark>
      {text.slice(idx + query.length)}
    </>
  )
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
  const hl = (text: string) => highlightText(text, searchText)

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
            {hl(event.input)}
          </div>
        )}
      </div>
    )
  }

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
                <span className="text-base-content/70 break-all">{hl(event.args)}</span>
              </div>
            )}
            {isComplete && (
              <div className="flex gap-2">
                <span className="text-base-content/30 shrink-0">result:</span>
                <span className="text-base-content/70 break-all whitespace-pre-wrap">{hl(event.result ?? '')}</span>
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
// AgentsPage
// ---------------------------------------------------------------------------

export default function AgentsPage() {
  // ── 公共状态 ──
  const [tab, setTab] = useState<'logs' | 'prompts'>('logs')
  const [selectedMode, setSelectedMode] = useState('all')
  const status = useDashboardStore(s => s.status)
  const currentMode = status?.agent_mode ?? '5_agent'

  // ── 日志视图状态 ──
  const agentEvents = useDashboardStore(s => s.agentEvents)
  const [pageSize, setPageSize] = useState(20)
  const [searchText, setSearchText] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [autoScroll, setAutoScroll] = useState(true)
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const streamRef = useRef<HTMLDivElement>(null)

  const toggleTool = useCallback((key: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev)
      if (next.has(key)) { next.delete(key) } else { next.add(key) }
      return next
    })
  }, [])

  const filteredEvents = useMemo(() => {
    let events = agentEvents
    if (selectedMode !== 'all') {
      const modeOrder = getAgentOrder(selectedMode)
      if (modeOrder.length > 0) {
        events = events.filter(e => modeOrder.includes(e.agent))
      } else {
        return []
      }
    }
    if (searchText) {
      const q = searchText.toLowerCase()
      events = events.filter(e => {
        const haystack = [e.input, e.output, e.tool, e.args, e.result, e.agent].filter(Boolean).join(' ').toLowerCase()
        return haystack.includes(q)
      })
    }
    return events
  }, [agentEvents, selectedMode, searchText])

  const totalPages = Math.max(1, Math.ceil(filteredEvents.length / pageSize))
  const safePage = Math.min(currentPage, totalPages)
  const paginatedEvents = useMemo(() => {
    const start = (safePage - 1) * pageSize
    return filteredEvents.slice(start, start + pageSize)
  }, [filteredEvents, safePage, pageSize])

  useEffect(() => { setCurrentPage(1) }, [selectedMode, searchText])
  useEffect(() => {
    if (autoScroll && safePage === totalPages && streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight
    }
  }, [paginatedEvents, autoScroll, safePage, totalPages])

  // ── 提示词视图状态 ──
  const [prompts, setPrompts] = useState<AgentPrompt[]>([])
  const [activePrompt, setActivePrompt] = useState('')
  const [promptText, setPromptText] = useState('')
  const [promptsLoading, setPromptsLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const activePromptRef = useRef('')

  useEffect(() => { activePromptRef.current = activePrompt }, [activePrompt])

  const loadPrompts = useCallback(async () => {
    try {
      const data = await fetchPrompts()
      setPrompts(data)
      const cur = activePromptRef.current
      if (cur && data.find(p => p.name === cur)) {
        setPromptText(data.find(p => p.name === cur)!.text)
      } else if (data.length > 0) {
        setActivePrompt(data[0].name)
        setPromptText(data[0].text)
      }
    } catch { /* */ }
    setPromptsLoading(false)
  }, [])

  useEffect(() => {
    if (tab === 'prompts') loadPrompts()
  }, [tab, loadPrompts])

  const handleSelectPrompt = useCallback((name: string) => {
    setActivePrompt(name)
    const p = prompts.find(p => p.name === name)
    if (p) setPromptText(p.text)
    setMsg('')
  }, [prompts])

  const handleSave = useCallback(async () => {
    if (!activePrompt) return
    setSaving(true)
    setMsg('')
    try {
      await updatePrompt(activePrompt, promptText)
      const reload = await reloadAgents()
      setMsg(reload.ok ? '已保存，Agent 已即时热重载' : '已保存，将在下个 tick 生效')
      await loadPrompts()
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '保存失败')
    }
    setSaving(false)
  }, [activePrompt, promptText, loadPrompts])

  const handleReset = useCallback(async () => {
    if (!activePrompt) return
    setSaving(true)
    setMsg('')
    try {
      await resetPrompt(activePrompt)
      setMsg('已重置为默认值')
      const data = await fetchPrompts()
      setPrompts(data)
      const def = data.find(p => p.name === activePrompt)?.text ?? ''
      setPromptText(def)
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '重置失败')
    }
    setSaving(false)
  }, [activePrompt])

  const activeP = prompts.find(p => p.name === activePrompt)
  const saveInfo = {
    label: activeP?.label ?? '',
    modified: activeP?.modified ?? false,
    lines: promptText.split('\n').length,
  }

  // 根据左侧方案过滤 Agent 列表（保持方案定义的顺序）
  const modeAgents = useMemo(() => {
    if (!prompts.length) return []
    if (selectedMode === 'all') return prompts
    const order = getAgentOrder(selectedMode)
    if (order.length === 0) return []
    // 按 order 顺序排列，过滤掉 prompts 中不存在的
    return order
      .map(name => prompts.find(p => p.name === name))
      .filter((p): p is AgentPrompt => !!p)
  }, [prompts, selectedMode])

  // 方案/标签切换时，自动纠正选中的 Agent
  const prevModeRef = useRef(selectedMode)
  useEffect(() => {
    if (tab !== 'prompts' || modeAgents.length === 0) {
      prevModeRef.current = selectedMode
      return
    }
    // 首次进入或方案变更
    const curActive = activePromptRef.current
    const modeChanged = prevModeRef.current !== selectedMode
    prevModeRef.current = selectedMode
    if (modeChanged || !curActive || !modeAgents.find(p => p.name === curActive)) {
      setActivePrompt(modeAgents[0].name)
      setPromptText(modeAgents[0].text)
    }
  }, [tab, selectedMode, modeAgents])

  // ── 公共 ──
  const hasEvents = agentEvents.length > 0
  const selectedLabel = MODE_LIST.find(m => m.key === selectedMode)?.label ?? '全部 Agent'

  // =========================================================================
  // 渲染
  // =========================================================================

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* ================================================================ */}
      {/* 左侧栏 — 方案选择（日志/提示词共享）                              */}
      {/* ================================================================ */}
      <div className="w-[188px] shrink-0 border-r border-base-300 bg-base-100 flex flex-col">
        <div className="px-3 py-3 text-xs text-base-content/40 font-medium tracking-wider">
          方案选择
        </div>
        <ul className="menu gap-[1.5px] flex-nowrap flex-1 overflow-y-auto">
          {MODE_LIST.map(item => {
            const agentLen = item.order.length
            const isActive = selectedMode === item.key
            return (
              <li key={item.key}>
                <a
                  onClick={() => setSelectedMode(item.key)}
                  className={`flex justify-between ${isActive ? 'menu-active' : ''}`}
                >
                  <span>{item.label}</span>
                  {agentLen > 0 && (
                    <span className="text-[10px] text-base-content/25 font-mono">{agentLen} agents</span>
                  )}
                </a>
              </li>
            )
          })}
        </ul>
        <div className="px-3 py-2 border-t border-base-200">
          <span className="text-[10px] text-base-content/30">
            当前: {MODE_LABEL[currentMode] ?? currentMode}
          </span>
        </div>
      </div>

      {/* ================================================================ */}
      {/* 右侧 — 双标签                                                     */}
      {/* ================================================================ */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* ── 标签栏 ── */}
        <div className="flex items-center border-b border-base-300 bg-base-100 px-3 shrink-0">
          <div role="tablist" className="tabs tabs-border">
            <a
              role="tab"
              className={`tab ${tab === 'logs' ? 'tab-active' : ''}`}
              onClick={() => setTab('logs')}
            >
              决策日志
            </a>
            <a
              role="tab"
              className={`tab ${tab === 'prompts' ? 'tab-active' : ''}`}
              onClick={() => setTab('prompts')}
            >
              提示词
            </a>
          </div>
        </div>

        {/* ============================================================ */}
        {/* 日志视图                                                      */}
        {/* ============================================================ */}
        {tab === 'logs' && (
          <div className="flex-1 flex flex-col min-w-0">
            {/* 顶栏 */}
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
              <div className="relative w-44">
                <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-base-content/30 pointer-events-none" />
                <FormInput
                  type="text"
                  size="xs"
                  placeholder="搜索..."
                  value={searchText}
                  onChange={setSearchText}
                  className="w-full pl-7 bg-base-200 text-xs border-0"
                />
              </div>
              <FormInput
                type="checkbox"
                size="xs"
                checked={autoScroll}
                onChange={setAutoScroll}
                label="自动滚动"
              />
            </div>

            {/* 日志流 */}
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

            {/* 分页 */}
            <div className="shrink-0 border-t border-base-200 bg-base-100 px-4 py-2">
              <Paginator
                size="small"
                current={safePage}
                total={filteredEvents.length}
                pageSize={pageSize}
                pageSizeOptions={[20, 50, 100]}
                showSizeChanger
                onChange={(p, ps) => { setCurrentPage(p); setPageSize(ps) }}
              />
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* 提示词视图                                                    */}
        {/* ============================================================ */}
        {tab === 'prompts' && (
          promptsLoading ? (
            <div className="flex items-center justify-center flex-1 text-sm text-base-content/40">
              加载中...
            </div>
          ) : (
            <div className="flex-1 flex flex-col min-w-0">
              {/* Agent 选择条 — 根据左侧方案过滤 */}
              <div className="flex items-center gap-1 px-4 py-2 bg-base-100 border-b border-base-300 shrink-0 overflow-x-auto">
                {modeAgents.length === 0 && (
                  <span className="text-xs text-base-content/30">当前方案无 Agent</span>
                )}
                {modeAgents.map(p => (
                  <button
                    key={p.name}
                    onClick={() => handleSelectPrompt(p.name)}
                    className={`btn btn-xs whitespace-nowrap ${
                      activePrompt === p.name ? 'btn-primary' : 'btn-ghost'
                    }`}
                  >
                    {p.label}
                    {p.modified && (
                      <span className="w-1.5 h-1.5 rounded-full bg-warning shrink-0 ml-1" title="已修改" />
                    )}
                  </button>
                ))}
              </div>

              {/* 编辑器 */}
              <PromptEditor
                value={promptText}
                onChange={setPromptText}
                saveInfo={saveInfo}
                msg={msg}
                onSave={handleSave}
                onReset={handleReset}
                saving={saving}
                placeholder="Agent 系统提示词..."
              />
            </div>
          )
        )}
      </div>
    </div>
  )
}
