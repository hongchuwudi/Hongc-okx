/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测结果卡片 — 收益率/胜率/夏普/回撤/盈亏比等 8 项 KPI
 */

import type { ResultCardsProps } from '@/types/props/props'

export default function ResultCards({ metrics, symbol }: ResultCardsProps) {
  const cards = [
    { label: '总收益率', value: `${(metrics.total_return_pct ?? 0).toFixed(2)}%`, color: (metrics.total_return_pct ?? 0) >= 0 ? 'text-success' : 'text-error' },
    { label: '胜率', value: `${(metrics.win_rate ?? 0).toFixed(1)}%` },
    { label: '夏普比率', value: (metrics.sharpe_ratio ?? 0).toFixed(2) },
    { label: '最大回撤', value: `${(metrics.max_drawdown_pct ?? 0).toFixed(2)}%`, color: 'text-warning' },
    { label: '盈亏比', value: (metrics.profit_factor ?? 0).toFixed(2) },
    { label: '总交易', value: String(metrics.total_trades ?? 0) },
    { label: '最终权益', value: `$${(metrics.final_equity ?? 0).toFixed(2)}` },
    { label: '盈利/亏损', value: `${metrics.winning_trades ?? '-'} / ${metrics.losing_trades ?? '-'}` },
  ]
  return (
    <div className="card bg-base-100 border border-base-300">
      <div className="card-body p-4">
        <h2 className="card-title text-base">绩效指标 — {symbol}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {cards.map(c => (
            <div key={c.label} className="stat bg-base-100 rounded-lg p-3">
              <div className="stat-title text-xs">{c.label}</div>
              <div className={`stat-value text-base md:text-lg ${c.color || ''}`}>{c.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
