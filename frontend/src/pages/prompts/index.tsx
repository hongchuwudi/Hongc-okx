/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: Agent 提示词管理页面 — 左侧列表 + PromptEditor 编辑 + 保存后即时热重载
 *
 * 包含:
 * - Sidebar — 左侧 Agent 列表
 * - PromptEditor — 通用编辑器（工具栏 + 设置面板 + 编辑区）
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchPrompts, updatePrompt, resetPrompt, reloadAgents } from '@/api/agents'
import PromptEditor from '@/components/PromptEditor'
import type { AgentPrompt } from '@/types/agents'

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<AgentPrompt[]>([])
  const [active, setActive] = useState('')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const activeRef = useRef('')

  useEffect(() => { activeRef.current = active }, [active])

  const load = useCallback(async () => {
    try {
      const data = await fetchPrompts()
      setPrompts(data)
      const cur = activeRef.current
      if (cur && data.find(p => p.name === cur)) {
        setText(data.find(p => p.name === cur)!.text)
      } else if (data.length > 0) {
        setActive(data[0].name)
        setText(data[0].text)
      }
    } catch { /* */ }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const handleSelect = useCallback((name: string) => {
    setActive(name)
    const p = prompts.find(p => p.name === name)
    if (p) setText(p.text)
    setMsg('')
  }, [prompts])

  const handleSave = useCallback(async () => {
    if (!active) return
    setSaving(true)
    setMsg('')
    try {
      await updatePrompt(active, text)
      // 触发即时热重载
      const reload = await reloadAgents()
      setMsg(reload.ok ? '已保存，Agent 已即时热重载' : '已保存，将在下个 tick 生效')
      await load()
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '保存失败')
    }
    setSaving(false)
  }, [active, text, load])

  const handleReset = useCallback(async () => {
    if (!active) return
    setSaving(true)
    setMsg('')
    try {
      await resetPrompt(active)
      setMsg('已重置为默认值')
      const data = await fetchPrompts()
      setPrompts(data)
      const def = data.find(p => p.name === active)?.text ?? ''
      setText(def)
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '重置失败')
    }
    setSaving(false)
  }, [active])

  const activePrompt = prompts.find(p => p.name === active)
  const saveInfo = {
    label: activePrompt?.label ?? '',
    modified: activePrompt?.modified ?? false,
    lines: text.split('\n').length,
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-base-content/40">
        加载中...
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* 左侧 Agent 列表 */}
      <nav className="w-48 shrink-0 border-r border-base-300 bg-base-100 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] text-base-content/40 font-medium tracking-wider">
          AGENT
        </div>
        {prompts.map(p => (
          <button
            key={p.name}
            onClick={() => handleSelect(p.name)}
            className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 transition-colors
              ${active === p.name
                ? 'bg-primary/10 text-primary font-medium border-r-2 border-primary'
                : 'hover:bg-base-200 text-base-content/70'}`}
          >
            <span className="truncate">{p.label}</span>
            {p.modified && (
              <span className="w-1.5 h-1.5 rounded-full bg-warning shrink-0" title="已修改" />
            )}
          </button>
        ))}
      </nav>

      {/* 右侧编辑器 */}
      <PromptEditor
        value={text}
        onChange={setText}
        saveInfo={saveInfo}
        msg={msg}
        onSave={handleSave}
        onReset={handleReset}
        saving={saving}
        placeholder="Agent 系统提示词..."
      />
    </div>
  )
}
