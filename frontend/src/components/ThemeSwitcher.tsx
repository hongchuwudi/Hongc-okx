/**
 * 创建时间: 2026-06-15
 * 作者: hongchuwudi
 * 描述: 主题切换 — daisyUI dropdown 四选一
 *
 * 包含:
 * - 组件: ThemeSwitcher — 主题下拉切换
 */

import { Palette } from 'lucide-react'
import { useThemeStore } from '@/stores/themeStore'
import { THEMES } from '@/constants/theme'
import type { ThemeMode } from '@/types/theme'

export default function ThemeSwitcher() {
  const theme = useThemeStore(s => s.theme)
  const setTheme = useThemeStore(s => s.setTheme)

  return (
    <div className="dropdown dropdown-end">
      <button type="button" tabIndex={0} className="btn btn-ghost btn-sm h-8 w-8 p-0 rounded-full" title="切换主题">
        <Palette size={16} className="text-base-content/60" />
      </button>
      <ul tabIndex={0} className="dropdown-content menu menu-sm w-32 rounded-box bg-base-200 shadow-lg border border-base-300 z-50 mt-1 p-0 [&_li_a]:rounded-none">
        {THEMES.map(t => (
          <li key={t.id}>
            <a
              className={theme.id === t.id ? 'active' : ''}
              onClick={() => setTheme(t.id as ThemeMode)}
            >
              {t.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
