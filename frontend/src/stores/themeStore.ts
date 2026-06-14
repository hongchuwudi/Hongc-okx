/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 主题状态 store — zustand 实现，localStorage 持久化 + DOM 同步
 */

import { create } from 'zustand'
import { DEFAULT_THEME, STORAGE_KEY, getThemeById } from '@/constants/theme'
import type { ThemeConfig, ThemeMode } from '@/types/theme'

function loadTheme(): ThemeConfig {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return getThemeById(saved)
  } catch { /* */ }
  return DEFAULT_THEME
}

interface ThemeStore {
  theme: ThemeConfig
  isDark: boolean
  setTheme: (id: ThemeMode) => void
}

export const useThemeStore = create<ThemeStore>((set) => {
  const initial = loadTheme()
  document.documentElement.dataset.theme = initial.daisy

  return {
    theme: initial,
    isDark: initial.id === 'dark',

    setTheme: (id: ThemeMode) => {
      const t = getThemeById(id)
      document.documentElement.dataset.theme = t.daisy
      set({ theme: t, isDark: t.id === 'dark' })
      try { localStorage.setItem(STORAGE_KEY, id) } catch { /* */ }
    },
  }
})
