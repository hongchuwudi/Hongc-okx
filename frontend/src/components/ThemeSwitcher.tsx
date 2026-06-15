/**
 * 创建时间: 2026-06-15
 * 作者: hongchuwudi
 * 描述: 主题切换按钮 — Sun/Moon 图标一键切换
 */

import { Sun, Moon } from 'lucide-react'
import { useThemeStore } from '@/stores/themeStore'

export default function ThemeSwitcher() {
  const theme = useThemeStore(s => s.theme)
  const setTheme = useThemeStore(s => s.setTheme)
  const isDark = theme.id === 'dark'

  return (
    <button
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      className="btn btn-ghost btn-sm h-8 w-8 p-0 rounded-full"
      title={isDark ? '切换浅色' : '切换深色'}
    >
      {isDark ? (
        <Sun size={18} className="text-warning" />
      ) : (
        <Moon size={18} className="text-base-content/60" />
      )}
    </button>
  )
}
