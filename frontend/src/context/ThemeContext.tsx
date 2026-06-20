/**
 * 创建时间: 2026-06-15
 * 作者: hongchuwudi
 * 描述: 主题上下文 — 全局主题状态 + localStorage 持久化 + Ant Design 同步
 *
 * 包含:
 * - ThemeProvider — 主题 Context Provider
 * - useTheme — 消费 Hook
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { ConfigProvider } from 'antd'
import { DEFAULT_THEME, STORAGE_KEY, getThemeById } from '@/constants/theme'
import type { ThemeConfig, ThemeMode } from '@/types/theme'

interface ThemeCtxValue {
  /** 当前主题配置 */
  theme: ThemeConfig
  /** 切换主题 */
  setTheme: (id: ThemeMode) => void
}

const Ctx = createContext<ThemeCtxValue | null>(null)

/** 从 localStorage 恢复主题 */
function loadTheme(): ThemeConfig {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return getThemeById(saved)
  } catch { /* localStorage 不可用时忽略 */ }
  return DEFAULT_THEME
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  // useState 初始化器在首帧渲染前同步执行，避免样式闪烁
  const [theme, setThemeState] = useState<ThemeConfig>(() => {
    const t = loadTheme()
    document.documentElement.dataset.theme = t.daisy
    return t
  })

  const setTheme = useCallback((id: ThemeMode) => {
    const t = getThemeById(id)
    document.documentElement.dataset.theme = t.daisy  // 同步切换，无闪烁
    setThemeState(t)
    try { localStorage.setItem(STORAGE_KEY, id) } catch { /* */ }
  }, [])

  const antdCfg = {
    algorithm: theme.antdAlgorithm,
    token: { colorPrimary: '#3370FF', borderRadius: 10 },
  }

  return (
    <Ctx.Provider value={{ theme, setTheme }}>
      <ConfigProvider theme={antdCfg}>
        {children}
      </ConfigProvider>
    </Ctx.Provider>
  )
}

/** 消费 Hook：获取当前主题和切换方法 */
export function useTheme(): ThemeCtxValue {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
