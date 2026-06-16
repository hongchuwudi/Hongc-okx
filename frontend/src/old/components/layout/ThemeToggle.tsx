/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: ThemeToggle.tsx 主题切换
 * 描述: 主题切换组件，支持亮色/暗色模式切换，持久化到 localStorage
 *
 * 包含:
 * - Hook: useTheme — 主题状态管理 Hook，包含读写 localStorage 和切换逻辑
 * - 组件: ThemeToggle — 主题切换按钮组件
 */
import { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'

// 主题管理 Hook — 读写 localStorage 持久化，切换亮色/暗色模式
export function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme')
    return (saved === 'dark' ? 'dark' : 'light')
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggle = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  return { theme, toggle }
}

// 主题切换按钮 — 显示月亮/太阳图标切换暗色/亮色
export default function ThemeToggle({ theme, toggle }: { theme: string; toggle: () => void }) {
  return (
    <button
      onClick={toggle}
      className="btn btn-ghost btn-sm btn-circle"
      title={theme === 'light' ? '切换暗色模式' : '切换亮色模式'}
    >
      {theme === 'light' ? <Moon className="w-[18px] h-[18px]" /> : <Sun className="w-[18px] h-[18px]" />}
    </button>
  )
}
