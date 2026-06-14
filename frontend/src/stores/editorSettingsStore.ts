/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 编辑器设置 store — zustand 实现，字体/换行/Tab 等编辑器偏好
 */

import { create } from 'zustand'

export interface EditorSettings {
  fontSize: number
  tabSize: number
  wordWrap: boolean
}

const DEFAULTS: EditorSettings = { fontSize: 12, tabSize: 2, wordWrap: true }

interface EditorSettingsStore {
  settings: EditorSettings
  update: (partial: Partial<EditorSettings>) => void
  reset: () => void
}

export const useEditorSettingsStore = create<EditorSettingsStore>((set) => ({
  settings: { ...DEFAULTS },
  update: (partial) => set((s) => ({ settings: { ...s.settings, ...partial } })),
  reset: () => set({ settings: { ...DEFAULTS } }),
}))
