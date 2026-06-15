/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 导航布局 — 品牌左 + Tab 居中
 */

import { NavLink, Outlet } from 'react-router-dom'
import ThemeSwitcher from '@/components/ThemeSwitcher'

const TABS = [
  { path: '/', label: '仪表盘' },
  { path: '/backtest', label: '回测' },
  { path: '/logs', label: '日志' },
  { path: '/trades', label: '交易' },
  { path: '/decisions', label: '决策' },
  { path: '/prompts', label: '提示词' },
]

export default function AppLayout() {
  return (
    <div className="flex flex-col min-h-dvh bg-base-200">
      <header className="sticky top-0 z-[100] bg-base-100 border-b border-base-300 animate-[slideDown_0.45s_cubic-bezier(0.16,1,0.3,1)]">
        <div className="flex items-center h-11 px-3">
          <span className="text-[17px] font-bold text-primary tracking-tight shrink-0 mr-4">
            OKX AI
          </span>

          <nav className="flex items-center gap-1">
            {TABS.map((tab) => (
              <NavLink
                key={tab.path}
                to={tab.path}
                end={tab.path === '/'}
                className={({ isActive }) =>
                  `relative px-3 py-1.5 text-[14px] rounded-md transition-colors duration-200
                   ${isActive ? 'text-primary font-semibold' : 'text-base-content/60 hover:text-primary'}`
                }
              >
                {({ isActive }) => (
                  <>
                    {tab.label}
                    {isActive && (
                      <span className="absolute bottom-[-12px] left-1/2 -translate-x-1/2 w-5 h-[3px] rounded-full bg-primary animate-[reveal_0.3s_cubic-bezier(0.16,1,0.3,1)]" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto">
            <ThemeSwitcher />
          </div>
        </div>
      </header>

      <main className="flex-1 animate-[fadeUp_0.5s_cubic-bezier(0.16,1,0.3,1)]">
        <Outlet />
      </main>
    </div>
  )
}
