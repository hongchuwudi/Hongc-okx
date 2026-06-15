/**
 * Created: 2026-06-12
 * Author: hongchuwudi
 * Description: 仪表盘页面 — 左配置 + 右(顶栏 + K线∥3D场景 + 持仓卡片 + Agent日志)
 */

import { useState, useCallback } from 'react'
import { useDashboardStore } from '@/stores/dashboardStore'
import StatusBar from './components/StatusBar'
import ConfigSidebar from './components/ConfigSidebar'
import KlineCard from './components/KlineCard'
import PositionCard from './components/PositionCard'
import AgentLogCard from './components/AgentLogCard'
import TradingScene from './components/animation-scene/TradingScene'

export default function Dashboard() {
  const status = useDashboardStore(s => s.status)
  const wsConnected = useDashboardStore(s => s.wsConnected)
  const refresh = useDashboardStore(s => s.refresh)
  const market = status?.market ?? null
  const position = status?.position ?? null
  const aiSignal = status?.ai_signal ?? null

  // 配置变更 → K 线图 + 状态全部立即刷新
  const [refreshKey, setRefreshKey] = useState(0)
  const onConfigChange = useCallback(() => {
    setRefreshKey(k => k + 1)
    refresh()
  }, [refresh])

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* 左侧：运行时配置 */}
      <div className="w-52 shrink-0">
        <ConfigSidebar onConfigChange={onConfigChange} />
      </div>

      {/* 右侧：内容区（可滚动） */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <StatusBar
          agentMode={status?.agent_mode ?? ''}
          market={market}
          position={position}
          aiSignal={aiSignal}
          wsConnected={wsConnected}
        />
        {/* K线 ∥ 3D 场景 */}
        <div className="grid grid-cols-2 gap-2 px-2 pt-2 pb-1" style={{ height: 'min(calc(100vh - 24rem), 380px)' }}>
          <KlineCard refreshKey={refreshKey} />
          <div className="card bg-base-100 border border-base-300 overflow-hidden">
            <TradingScene />
          </div>
        </div>
        {/* 持仓详情卡片 — 无持仓时显示空态 */}
        <div className="px-2 pb-1 shrink-0">
          {position && market ? (
            <PositionCard
              position={position}
              currentPrice={market.price}
              leverage={status?.account?.leverage ?? 10}
              stopLoss={aiSignal?.stop_loss}
              takeProfit={aiSignal?.take_profit}
            />
          ) : (
            <div className="card bg-base-100 border border-base-300">
              <div className="card-body p-3 text-center text-sm text-base-content/40">
                当前无持仓
              </div>
            </div>
          )}
        </div>
        {/* Agent 实时日志卡片 */}
        <div className="px-2 pb-2 shrink-0">
          <AgentLogCard />
        </div>
      </div>
    </div>
  )
}
