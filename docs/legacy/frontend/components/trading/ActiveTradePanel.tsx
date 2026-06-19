/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: ActiveTradePanel.tsx 活跃交易面板
 * 描述: 活跃交易面板，展示当前持仓状态、未实现盈亏和 AI Agent 团队决策详情
 *
 * 包含:
 * - 函数: fmtUSD — 美元格式化
 * - 函数: parseAgentReport — 解析 JSON 格式的 Agent 报告
 * - 组件: ActiveTradePanel — 活跃交易信息卡片
 */
import { TrendingUp, TrendingDown, Shield, Target, Brain, BarChart3, Users } from 'lucide-react'
import type { Position, AiSignal } from '../../types/dashboard'

// 美元金额格式化，处理 null/NaN 异常值
function fmtUSD(n: number): string {
  if (n == null || isNaN(n)) return '--'
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 解析 JSON 格式的 Agent 决策报告，提取 reason 和各 Agent 分析文本
function parseAgentReport(reason: string): { reason: string; agents?: Record<string, string> } | null {
  try { return JSON.parse(reason) }
  catch { return null }
}

// 活跃交易面板 — 展示持仓 PnL、方向、入场价/标记价和 AI Agent 决策详情
export default function ActiveTradePanel({ position, signal, btcPrice }: {
  position: Position | null; signal: AiSignal; btcPrice: number
}) {
  const agentReport = parseAgentReport(signal.reason || '')
  const displayReason = agentReport?.reason || signal.reason || 'analyzing...'
  const agents = agentReport?.agents

  return (
    <div className="card-dash bg-base-200 flex flex-col h-full">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-[16px] h-[16px] text-primary" />
        <span className="text-[12px] font-semibold text-base-content">AI Agent Team</span>
        {agents && <Users className="w-[14px] h-[14px] text-success ml-auto" />}
        {position && (
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${position.side === 'long' ? 'text-success bg-success/10 border-success/25' : 'text-error bg-error/10 border-error/25'}`}>
            {position.side === 'long' ? 'Long' : 'Short'}
          </span>
        )}
      </div>

      {/* no position */}
      {!position && (
        <div className="flex-1 flex flex-col items-center justify-center text-center gap-2">
          <div className="text-[40px] opacity-20">WAIT</div>
          <div className="text-[13px] text-base-content/60 font-medium">Waiting for signal</div>
          <div className="text-[11px] text-base-content/40 max-w-[200px] leading-relaxed">{displayReason}</div>
        </div>
      )}

      {/* has position */}
      {position && (
        <div className="flex-1 flex flex-col gap-3">
          <div className="text-center py-2 rounded-xl bg-base-100/50 border border-base-300">
            <div className="text-[10px] text-base-content/40 font-semibold uppercase mb-1">Unrealized PnL</div>
            <div className={`text-[28px] font-extrabold tabular-nums flex items-center justify-center gap-1.5 ${position.unrealized_pnl >= 0 ? 'text-success' : 'text-error'}`}>
              {position.unrealized_pnl >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
              {position.unrealized_pnl >= 0 ? '+' : ''}{position.unrealized_pnl.toFixed(2)}
            </div>
            <div className="text-[11px] text-base-content/40 mt-0.5">USDT</div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg bg-base-100/50 py-2"><div className="text-[10px] text-base-content/40 mb-0.5">Entry</div><div className="text-[15px] font-bold tabular-nums text-base-content">{fmtUSD(position.entry_price)}</div></div>
            <div className="rounded-lg bg-base-100/50 py-2"><div className="text-[10px] text-base-content/40 mb-0.5">Mark</div><div className="text-[15px] font-bold tabular-nums text-base-content">{fmtUSD(btcPrice)}</div></div>
            <div className="rounded-lg bg-base-100/50 py-2"><div className="text-[10px] text-base-content/40 mb-0.5">Size</div><div className="text-[15px] font-bold tabular-nums text-base-content">{position.size} ct</div></div>
            <div className="rounded-lg bg-base-100/50 py-2"><div className="text-[10px] text-base-content/40 mb-0.5">ROE</div><div className={`text-[15px] font-bold tabular-nums ${position.entry_price > 0 ? (btcPrice >= position.entry_price ? 'text-success' : 'text-error') : 'text-base-content'}`}>
              {position.entry_price > 0 ? ((btcPrice - position.entry_price) / position.entry_price * (position.side === 'long' ? 1 : -1) * 100).toFixed(2) + '%' : '--'}
            </div></div>
          </div>
        </div>
      )}

      {/* Agent reports */}
      <div className="mt-auto pt-3 border-t border-base-300">
        <div className="flex items-center gap-1.5 mb-2">
          <BarChart3 className="w-[14px] h-[14px] text-base-content/40" />
          <span className="text-[11px] text-base-content/40 font-semibold uppercase">Decision</span>
          <span className={`text-[11px] font-bold ml-auto ${signal.signal === 'BUY' ? 'text-success' : signal.signal === 'SELL' ? 'text-error' : 'text-warning'}`}>
            {signal.signal}
          </span>
        </div>

        {agents ? (
          <div className="space-y-1.5 mb-2">
            <div className="text-[11px] text-base-content/70 leading-relaxed bg-base-100/50 rounded-lg p-2">
              {displayReason}
            </div>
            <details className="text-[10px]" open>
              <summary className="text-primary cursor-pointer font-semibold">Agent Analysis</summary>
              <div className="mt-1 space-y-1 pl-2 border-l-2 border-primary/30">
                {agents.scheduler && <div className="text-base-content/50"><span className="text-amber-400 font-semibold">调度师:</span> {agents.scheduler}</div>}
                {agents.analyst && <div className="text-base-content/50"><span className="text-warning font-semibold">分析师:</span> {agents.analyst}</div>}
                {agents.reviewer && <div className="text-base-content/50"><span className="text-info font-semibold">复盘师:</span> {agents.reviewer}</div>}
                {agents.risk && <div className="text-base-content/50"><span className="text-error font-semibold">风控官:</span> {agents.risk}</div>}
                {agents.trader && <div className="text-base-content/50"><span className="text-success font-semibold">交易员:</span> {agents.trader}</div>}
              </div>
            </details>
          </div>
        ) : (
          <div className="text-[11px] text-base-content/60 leading-relaxed mb-2 line-clamp-3">{displayReason}</div>
        )}

        <div className="grid grid-cols-2 gap-1.5">
          <div className="flex items-center gap-1 text-[10px] text-error/80"><Shield className="w-3 h-3" />SL {fmtUSD(signal.stop_loss)}</div>
          <div className="flex items-center gap-1 text-[10px] text-success/80"><Target className="w-3 h-3" />TP {fmtUSD(signal.take_profit)}</div>
        </div>
      </div>
    </div>
  )
}
