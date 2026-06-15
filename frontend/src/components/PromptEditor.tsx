/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 通用提示词编辑器 — 工具栏 + 设置面板 + 编辑区，支持字体/换行/主题
 *
 * 包含:
 * - PromptEditor — 主组件，暴露 value/onChange/saveInfo 等接口
 * - EditorToolbar — 顶部工具栏（设置按钮 + 元信息 + 操作按钮）
 * - EditorSettingsBar — 展开的设置面板（字体/换行/Tab）
 */

import { useState, useCallback } from 'react'
import { useEditorSettingsStore } from '@/stores/editorSettingsStore'
import { useThemeStore } from '@/stores/themeStore'
import { Settings, RotateCcw, Save, Minus, Plus, WrapText } from 'lucide-react'

interface SaveInfo {
  label: string
  modified: boolean
  lines: number
}

interface Props {
  value: string
  onChange: (value: string) => void
  saveInfo: SaveInfo
  msg: string
  onSave: () => void
  onReset: () => void
  saving: boolean
  placeholder?: string
}

export default function PromptEditor({
  value, onChange, saveInfo, msg, onSave, onReset, saving, placeholder,
}: Props) {
  const settings = useEditorSettingsStore(s => s.settings)
  const update = useEditorSettingsStore(s => s.update)
  const theme = useThemeStore(s => s.theme)
  const isDark = theme.id === 'dark'
  const [showSettings, setShowSettings] = useState(false)

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* 工具栏 */}
      <EditorToolbar
        saveInfo={saveInfo}
        onSave={onSave}
        onReset={onReset}
        saving={saving}
        showSettings={showSettings}
        onToggleSettings={() => setShowSettings(!showSettings)}
      />

      {/* 设置面板 — 展开时 28px */}
      {showSettings && (
        <EditorSettingsBar
          fontSize={settings.fontSize}
          tabSize={settings.tabSize}
          wordWrap={settings.wordWrap}
          isDark={isDark}
          onFontSize={(n) => update({ fontSize: n })}
          onTabSize={(n) => update({ tabSize: n })}
          onWordWrap={(v) => update({ wordWrap: v })}
        />
      )}

      {/* 消息提示 — 有消息时占一行 */}
      {msg && (
        <MsgBar text={msg} />
      )}

      {/* 编辑区 */}
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        className="flex-1 p-4 font-mono resize-none outline-none border-0 transition-colors"
        style={{
          fontSize: `${settings.fontSize}px`,
          lineHeight: 1.75,
          tabSize: settings.tabSize,
          whiteSpace: settings.wordWrap ? 'pre-wrap' : 'pre',
          backgroundColor: isDark ? '#1a1a2e' : '#f4f4f5',
          color: isDark ? '#cdd6f4' : '#18181b',
        }}
        spellCheck={false}
        placeholder={placeholder ?? ''}
      />
    </div>
  )
}

// === 工具栏 ===

interface ToolbarProps {
  saveInfo: SaveInfo
  onSave: () => void
  onReset: () => void
  saving: boolean
  showSettings: boolean
  onToggleSettings: () => void
}

function EditorToolbar({ saveInfo, onSave, onReset, saving, showSettings, onToggleSettings }: ToolbarProps) {
  return (
    <div className="flex items-center gap-2 px-3 h-8 bg-base-100 border-b border-base-300 shrink-0">
      {/* 设置按钮 */}
      <button
        onClick={onToggleSettings}
        className={`btn btn-xs btn-ghost p-0 w-6 h-6 ${showSettings ? 'text-primary' : 'text-base-content/40'}`}
        title="编辑器设置"
      >
        <Settings size={13} />
      </button>

      {/* 文件名 */}
      <span className="text-xs font-medium">{saveInfo.label}</span>
      {saveInfo.modified && (
        <span className="badge badge-xs badge-warning text-[10px]">已修改</span>
      )}

      {/* 右侧信息 + 操作 */}
      <span className="text-[10px] text-base-content/30 ml-auto">{saveInfo.lines} 行</span>
      <button
        onClick={onReset}
        disabled={saving || !saveInfo.modified}
        className="btn btn-xs btn-ghost text-base-content/50"
      >
        <RotateCcw size={11} className="mr-1" />
        重置
      </button>
      <button
        onClick={onSave}
        disabled={saving}
        className="btn btn-xs btn-primary"
      >
        <Save size={11} className="mr-1" />
        {saving ? '...' : '保存'}
      </button>
    </div>
  )
}

// === 设置面板 ===

interface SettingsBarProps {
  fontSize: number
  tabSize: number
  wordWrap: boolean
  isDark: boolean
  onFontSize: (n: number) => void
  onTabSize: (n: number) => void
  onWordWrap: (v: boolean) => void
}

const FONT_SIZES = [10, 11, 12, 13, 14, 16, 18]
const TAB_SIZES = [2, 4, 8]

function EditorSettingsBar({ fontSize, tabSize, wordWrap, isDark, onFontSize, onTabSize, onWordWrap }: SettingsBarProps) {
  const decFont = () => { const i = FONT_SIZES.indexOf(fontSize); if (i > 0) onFontSize(FONT_SIZES[i - 1]) }
  const incFont = () => { const i = FONT_SIZES.indexOf(fontSize); if (i < FONT_SIZES.length - 1) onFontSize(FONT_SIZES[i + 1]) }

  return (
    <div className="flex items-center gap-4 px-3 h-7 bg-base-200 border-b border-base-300 shrink-0 text-[11px] select-none">
      {/* 字体大小 */}
      <div className="flex items-center gap-1">
        <span className="text-base-content/40">字体</span>
        <button onClick={decFont} className="btn btn-xs btn-ghost p-0 w-5 h-5" disabled={fontSize <= FONT_SIZES[0]}>
          <Minus size={10} />
        </button>
        <span className="w-6 text-center font-mono text-base-content/70">{fontSize}</span>
        <button onClick={incFont} className="btn btn-xs btn-ghost p-0 w-5 h-5" disabled={fontSize >= FONT_SIZES[FONT_SIZES.length - 1]}>
          <Plus size={10} />
        </button>
      </div>

      <span className="text-base-content/20">|</span>

      {/* 换行 */}
      <button
        onClick={() => onWordWrap(!wordWrap)}
        className={`btn btn-xs btn-ghost h-5 gap-1 ${wordWrap ? 'text-primary' : 'text-base-content/40'}`}
      >
        <WrapText size={10} />
        <span>{wordWrap ? '自动换行' : '不换行'}</span>
      </button>

      <span className="text-base-content/20">|</span>

      {/* Tab 宽度 */}
      <div className="flex items-center gap-1">
        <span className="text-base-content/40">Tab</span>
        {TAB_SIZES.map(n => (
          <button
            key={n}
            onClick={() => onTabSize(n)}
            className={`btn btn-xs btn-ghost p-0 w-6 h-5 font-mono ${tabSize === n ? 'text-primary font-bold' : 'text-base-content/40'}`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  )
}

// === 消息条 ===

function MsgBar({ text }: { text: string }) {
  const isError = text.includes('失败')
  return (
    <div className={`px-4 py-1 text-xs shrink-0 ${isError ? 'bg-error/10 text-error' : 'bg-success/10 text-success'}`}>
      {text}
    </div>
  )
}
