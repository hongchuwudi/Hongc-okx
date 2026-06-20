/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 全局导航布局 — daisyUI navbar + tabs-border 实现路由导航
 *
 * 包含:
 * - 组件: AppLayout — 顶部导航栏 (navbar) + 标签式路由切换 (tabs) + 内容区 (Outlet)
 */

import { NavLink, Outlet } from 'react-router-dom'
import ThemeSwitcher from '@/components/ThemeSwitcher'

const TABS = [
  { path: '/', label: '仪表盘' },
  { path: '/backtest', label: '回测' },
  { path: '/agents', label: 'Agent' },
  { path: '/trades', label: '交易' },
  { path: '/decisions', label: '决策' },
]

export default function AppLayout() {
  return (
    <div className="flex flex-col min-h-dvh bg-base-200">
      {/* ── 顶部导航栏 ── */}
      <header className="sticky top-0 z-[100] navbar bg-base-100 border-b border-base-300 min-h-0 py-0 animate-[slideDown_0.45s_cubic-bezier(0.16,1,0.3,1)]">
        {/* 左侧: 品牌 */}
        <div className="navbar-start">
          <span className="text-lg font-bold text-primary tracking-tight">
            OKX AI
          </span>
        </div>

        {/* 中间: 路由标签 */}
        <div className="navbar-center">
          <nav role="tablist" className="tabs tabs-border">
            {TABS.map((tab) => (
              <NavLink
                key={tab.path}
                to={tab.path}
                end={tab.path === '/'}
                role="tab"
                className={({ isActive }) =>
                  `tab ${isActive ? 'tab-active' : ''}`
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* 右侧: 主题切换 */}
        <div className="navbar-end">
          <ThemeSwitcher />
        </div>
      </header>

      {/* ── 内容区 ── */}
      <main className="flex-1 animate-[fadeUp_0.5s_cubic-bezier(0.16,1,0.3,1)]">
        <Outlet />
      </main>
    </div>
  )
}
