/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测交易明细表格
 */

import type { TradeTableProps } from '@/types/props/props'

export default function TradeTable({ trades }: TradeTableProps) {
  if (trades.length === 0) return null
  return (
    <div className="card bg-base-100 border border-base-300">
      <div className="card-body p-4">
        <h2 className="card-title text-base">交易明细 ({trades.length}笔)</h2>
        <div className="overflow-x-auto max-h-80 overflow-y-auto">
          <table className="table table-sm table-zebra">
            <thead>
              <tr>
                <th>时间</th>
                <th>方向</th>
                <th>入场价</th>
                <th>出场价</th>
                <th>持仓K线</th>
                <th>盈亏(USDT)</th>
                <th className="hidden md:table-cell">类型</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr key={i}>
                  <td className="text-xs">{t.timestamp}</td>
                  <td>
                    <span className={`badge badge-xs ${t.side === 'long' ? 'badge-success' : 'badge-error'}`}>
                      {t.side === 'long' ? '多' : '空'}
                    </span>
                  </td>
                  <td className="text-xs font-mono">${t.entry?.toFixed(4)}</td>
                  <td className="text-xs font-mono">{t.exit ? `$${t.exit.toFixed(4)}` : '—'}</td>
                  <td className="text-xs">{t.bars_held}</td>
                  <td className={`text-xs font-semibold ${(t.pnl ?? 0) >= 0 ? 'text-success' : 'text-error'}`}>
                    {(t.pnl ?? 0) >= 0 ? '+' : ''}{(t.pnl ?? 0).toFixed(4)}
                  </td>
                  <td className="text-xs text-base-content/60 hidden md:table-cell">
                    {t.action === 'open' ? '开仓' : t.confidence}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
