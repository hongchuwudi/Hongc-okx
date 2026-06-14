/**
 * Created: 2026-06-16
 * Author: hongchuwudi
 * Description: 持仓详情卡片 — OKX 风格多格展示：方向/杠杆/数量/价值/均价/标记价/浮盈/强平价/保证金/止盈止损
 */

import { SIDE_LABEL, SIDE_COLOR } from '@/constants/position'
import type { PositionCardProps } from '@/types/props/props'

function fmt(p: number): string {
  if (p === 0) return '0.00'
  if (p < 1) return p.toFixed(6)
  if (p < 100) return p.toFixed(4)
  return p.toFixed(2)
}

function usdt(n: number): string {
  return n.toFixed(2) + ' USDT'
}

export default function PositionCard({
  position, currentPrice, leverage, stopLoss, takeProfit,
}: PositionCardProps) {
  const side = position.side
  const colors = SIDE_COLOR[side] ?? SIDE_COLOR.long
  const unrealizedPnl = position.unrealized_pnl ?? 0
  const pnlPct = position.pnl_pct ?? 0
  const markPrice = position.mark_price || currentPrice
  const margin = position.margin ?? 0
  const notional = position.notional ?? 0
  const liqPrice = position.liquidation_price ?? 0

  return (
    <div className="card bg-base-100 border border-base-300">
      <div className="card-body p-3">

        {/* 第一行：方向 + 杠杆 + 张数 + 盈亏 */ }
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={`badge badge-sm ${colors.bg} text-white font-bold`}>
              {SIDE_LABEL[side] ?? side}
            </span>
            <span className="badge badge-sm badge-outline text-[11px]">{leverage}x</span>
            <span className="text-xs text-base-content/50">{position.size} 张</span>
            {notional > 0 && (
              <span className="text-[11px] text-base-content/30 font-mono">
                {usdt(notional)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-bold font-mono ${unrealizedPnl >= 0 ? 'text-success' : 'text-error'}`}>
              {unrealizedPnl >= 0 ? '+' : ''}{unrealizedPnl.toFixed(2)} USDT
            </span>
            <span className={`badge badge-xs font-mono ${pnlPct >= 0 ? 'badge-success' : 'badge-error'}`}>
              {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* 盈亏进度条 */ }
        <div className="w-full h-1 bg-base-200 rounded-full mb-2.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${unrealizedPnl >= 0 ? 'bg-success' : 'bg-error'}`}
            style={{ width: `${Math.min(Math.abs(pnlPct) * 2, 100)}%` }}
          />
        </div>

        {/* 第三行：OKX 风格 2x4 网格 */ }
        <div className="grid grid-cols-4 gap-x-3 gap-y-1.5 text-xs">
          {/* 开仓均价 */ }
          <div>
            <div className="text-[10px] text-base-content/40">开仓均价</div>
            <div className="font-mono font-medium mt-0.5">{fmt(position.entry_price)}</div>
          </div>
          {/* 标记价格 */ }
          <div>
            <div className="text-[10px] text-base-content/40">标记价格</div>
            <div className={`font-mono font-medium mt-0.5 ${markPrice >= position.entry_price ? 'text-success' : 'text-error'}`}>
              {fmt(markPrice)}
            </div>
          </div>
          {/* 强平价格 */ }
          <div>
            <div className="text-[10px] text-base-content/40">强平价格</div>
            <div className="font-mono font-medium mt-0.5 text-base-content/50">
              {liqPrice > 0 ? fmt(liqPrice) : '--'}
            </div>
          </div>
          {/* 保证金 */ }
          <div>
            <div className="text-[10px] text-base-content/40">保证金</div>
            <div className="font-mono font-medium mt-0.5">
              {margin > 0 ? usdt(margin) : '--'}
            </div>
          </div>
          {/* 当前价格 */ }
          <div>
            <div className="text-[10px] text-base-content/40">当前价格</div>
            <div className={`font-mono font-medium mt-0.5 ${currentPrice >= position.entry_price ? 'text-success' : 'text-error'}`}>
              {fmt(currentPrice)}
            </div>
          </div>
          {/* 未实现盈亏 */ }
          <div>
            <div className="text-[10px] text-base-content/40">浮盈(USD/%)</div>
            <div className={`font-mono font-medium mt-0.5 ${unrealizedPnl >= 0 ? 'text-success' : 'text-error'}`}>
              {unrealizedPnl >= 0 ? '+' : ''}{unrealizedPnl.toFixed(2)} / {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
            </div>
          </div>
          {/* 止损价 */ }
          <div>
            <div className="text-[10px] text-base-content/40">止损价</div>
            <div className="font-mono font-medium mt-0.5 text-error">
              {stopLoss ? fmt(stopLoss) : '--'}
            </div>
          </div>
          {/* 止盈价 */ }
          <div>
            <div className="text-[10px] text-base-content/40">止盈价</div>
            <div className="font-mono font-medium mt-0.5 text-success">
              {takeProfit ? fmt(takeProfit) : '--'}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
