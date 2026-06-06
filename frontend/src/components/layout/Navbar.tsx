import { RefreshCw, LayoutDashboard, FlaskConical } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

interface NavbarProps {
  tab: 'live' | 'backtest'; onTab: (t: 'live' | 'backtest') => void
  onRefresh: () => void; loading: boolean
  autoRefresh: boolean; onToggleAuto: () => void
  theme: string; onToggleTheme: () => void
  lastUpdated: number | null
  statusRunning: boolean
}

export default function Navbar({ tab, onTab, onRefresh, loading, autoRefresh, onToggleAuto, theme, onToggleTheme, lastUpdated, statusRunning }: NavbarProps) {
  const ago = lastUpdated ? Math.round((Date.now() - lastUpdated) / 1000) : null

  return (
    <div className="navbar bg-base-200 border-b border-base-300 px-0 md:px-2 mb-3 rounded-xl min-h-0 py-2">
      <div className="navbar-start gap-2">
        <span className="text-[16px] font-bold text-base-content tracking-tight ml-2 md:ml-0">BTC 交易</span>

        {/* 状态指示点 — 集成在导航栏 */}
        <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold ${statusRunning ? 'text-success' : 'text-base-content/40'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${statusRunning ? 'bg-success animate-pulse' : 'bg-base-content/30'}`} />
          {statusRunning ? '运行中' : '待启动'}
        </span>
      </div>

      <div className="navbar-center hidden md:flex">
        <div className="flex gap-0.5 rounded-lg p-0.5 bg-base-100 border border-base-300">
          <button onClick={() => onTab('live')} className={`flex items-center gap-1.5 px-3 py-1 text-[12px] font-semibold rounded-lg transition-colors ${tab === 'live' ? 'bg-primary text-primary-content' : 'text-base-content/60 hover:text-base-content'}`}>
            <LayoutDashboard className="w-[14px] h-[14px]" />监控
          </button>
          <button onClick={() => onTab('backtest')} className={`flex items-center gap-1.5 px-3 py-1 text-[12px] font-semibold rounded-lg transition-colors ${tab === 'backtest' ? 'bg-primary text-primary-content' : 'text-base-content/60 hover:text-base-content'}`}>
            <FlaskConical className="w-[14px] h-[14px]" />回测
          </button>
        </div>
      </div>

      <div className="navbar-end flex items-center gap-1">
        <div className="flex md:hidden gap-0.5 rounded-lg p-0.5 bg-base-100 border border-base-300 mr-1">
          <button onClick={() => onTab('live')} className={`px-2 py-0.5 text-[10px] font-semibold rounded-lg ${tab === 'live' ? 'bg-primary text-primary-content' : 'text-base-content/60'}`}>监控</button>
          <button onClick={() => onTab('backtest')} className={`px-2 py-0.5 text-[10px] font-semibold rounded-lg ${tab === 'backtest' ? 'bg-primary text-primary-content' : 'text-base-content/60'}`}>回测</button>
        </div>

        {ago !== null && (
          <span className="text-[10px] text-base-content/40 hidden sm:inline mr-1">
            {ago < 8 ? <span className="text-success">实时</span> : `${ago}s`}
          </span>
        )}

        <button className="btn btn-ghost btn-sm btn-square hidden sm:flex" onClick={onRefresh} disabled={loading} title="刷新">
          {loading ? <span className="loading loading-spinner loading-xs" /> : <RefreshCw className="w-[16px] h-[16px]" />}
        </button>
        <label className="hidden sm:flex items-center gap-1 text-base-content/60 text-[11px] cursor-pointer select-none px-1">
          <input type="checkbox" className="toggle toggle-xs" checked={autoRefresh} onChange={onToggleAuto} />
        </label>
        <ThemeToggle theme={theme} toggle={onToggleTheme} />
      </div>
    </div>
  )
}
