/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 编辑器设置状态管理 — 字体大小 / 换行 / Tab 宽度等偏好，全局共享
 *
 * 包含:
 * - EditorSettingsProvider — Context Provider
 * - useEditorSettings — 消费 Hook
 * - EditorSettings — 设置接口
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

export interface EditorSettings {
  fontSize: number        // 默认 12px
  tabSize: number         // 默认 2
  wordWrap: boolean       // 默认 true
}

const DEFAULTS: EditorSettings = { fontSize: 12, tabSize: 2, wordWrap: true }

const Ctx = createContext<{
  settings: EditorSettings
  update: (partial: Partial<EditorSettings>) => void
  reset: () => void
} | null>(null)

export function EditorSettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<EditorSettings>(DEFAULTS)

  const update = useCallback((partial: Partial<EditorSettings>) => {
    setSettings(prev => ({ ...prev, ...partial }))
  }, [])

  const reset = useCallback(() => setSettings(DEFAULTS), [])

  return (
    <Ctx.Provider value={{ settings, update, reset }}>
      {children}
    </Ctx.Provider>
  )
}

export function useEditorSettings() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useEditorSettings need EditorSettingsProvider')
  return ctx
}
