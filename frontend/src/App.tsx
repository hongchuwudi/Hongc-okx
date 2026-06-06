import { useState } from 'react'
import { DashboardProvider, useDashboard } from './context/DashboardContext'
import { useTheme } from './components/layout/ThemeToggle'
import Navbar from './components/layout/Navbar'
import KpiCard from './components/dashboard/KpiCard'
import KlineChart from './components/charts/KlineChart'
import AgentOffice from './components/agent/AgentOffice'
import EquityChart from './components/charts/EquityChart'
import ActiveTradePanel from './components/trading/ActiveTradePanel'
import PerformanceStats from './components/PerformanceStats'
import SignalDistributionChart from './components/charts/SignalDistributionChart'
import RecentTradesTable from './components/trading/RecentTradesTable'
import BacktestPanel from './components/backtest/BacktestPanel'
import { Wallet, TrendingUp, Zap, Bitcoin } from 'lucide-react'
import type { AccountInfo, BtcInfo } from './types/dashboard'

function fmtUSD(n: number): string {
  if (n == null || isNaN(n)) return '$—'
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function KpiStrip({ account, btc }: { account: AccountInfo; btc: BtcInfo }) {
  const btcDelta = btc.change != null ? `${btc.change >= 0 ? '+' : ''}${btc.change.toFixed(2)}%` : undefined
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-2">
      <KpiCard icon={Wallet}    iconBg="bg-primary/15"    label="余额"   value={fmtUSD(account.balance)} />
      <KpiCard icon={TrendingUp} iconBg="bg-success/15"   label="权益"   value={fmtUSD(account.equity)} />
      <KpiCard icon={Zap}       iconBg="bg-warning/15"    label="杠杆"   value={`${account.leverage || 1}x`} />
      <KpiCard icon={Bitcoin}   iconBg="bg-purple-500/15" label="BTC"    value={fmtUSD(btc.price)} delta={btcDelta} deltaUp={btc.change != null ? btc.change >= 0 : undefined} />
    </div>
  )
}

function Dashboard() {
  const { state, refresh, toggleAutoRefresh } = useDashboard()
  const { status, trades, equity, loading, error, autoRefresh } = state
  const [tab, setTab] = useState<'live' | 'backtest'>('live')
  const { theme, toggle } = useTheme()
  const running = status?.status === 'running'

  return (
    <>
      <Navbar
        tab={tab} onTab={setTab} onRefresh={refresh} loading={loading}
        autoRefresh={autoRefresh} onToggleAuto={toggleAutoRefresh}
        theme={theme} onToggleTheme={toggle}
        lastUpdated={state.lastUpdated}
        statusRunning={running}
      />

      {tab === 'live' && (
        <>
          {error && <div className="alert alert-error mb-3 py-2 text-sm"><span>{error}</span></div>}

          {/* KPI 紧凑条 */}
          {status && <KpiStrip account={status.account} btc={status.btc} />}

          {/* Agent 办公室场景 */}
          <div className="mb-2" style={{ minHeight: '380px' }}>
            <AgentOffice
              aiReason={status?.ai_signal?.reason || ''}
              lastUpdate={state.lastUpdated}
            />
          </div>

          {/* K线(3) + 交易面板(2) — 等高 */}
          <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-2 mb-2 items-stretch" style={{ minHeight: '400px' }}>
            <KlineChart />
            {status && (
              <ActiveTradePanel
                position={status.position}
                signal={status.ai_signal}
                btcPrice={status.btc.price}
              />
            )}
          </div>

          {/* 权益曲线 */}
          <div className="mb-2">
            <EquityChart data={equity} />
          </div>

          {/* 绩效 + 信号分布 */}
          <div className="grid grid-cols-1 md:grid-cols-[1fr_260px] gap-2 mb-2">
            <PerformanceStats performance={status?.performance ?? { total_pnl: 0, win_rate: 0, total_trades: 0 }} />
            <SignalDistributionChart trades={trades} />
          </div>

          {/* 交易记录 */}
          <RecentTradesTable trades={trades} />
        </>
      )}

      {tab === 'backtest' && <BacktestPanel />}

      <div className="text-center py-3 text-[10px] text-base-content/30">
        免责声明：本系统仅供学习研究，不构成投资建议
      </div>
    </>
  )
}

export default function App() {
  return <DashboardProvider><Dashboard /></DashboardProvider>
}
