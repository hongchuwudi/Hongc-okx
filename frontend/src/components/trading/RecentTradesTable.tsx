import { ScrollText, ArrowUp, ArrowDown, Minus } from 'lucide-react'
import type { Trade } from '../../types/dashboard'

function fmtTime(ts: string): string {
  if (!ts || ts === 'N/A') return '—'
  return ts.length >= 16 ? ts.substring(5, 16) : ts
}

export default function RecentTradesTable({ trades }: { trades: Trade[] }) {
  const recent = trades.slice(-20).reverse()
  if (recent.length === 0) {
    return (
      <div className="card-dash bg-base-200">
        <div className="flex items-center gap-2 mb-3"><ScrollText className="w-[18px] h-[18px] text-base-content/60" /><span className="text-[13px] font-semibold text-base-content">近期交易</span></div>
        <div className="text-center py-10 text-[13px] text-base-content/40">暂无交易记录</div>
      </div>
    )
  }

  return (
    <div className="card-dash bg-base-200">
      <div className="flex items-center gap-2 mb-3">
        <ScrollText className="w-[18px] h-[18px] text-base-content/60" />
        <span className="text-[13px] font-semibold text-base-content">近期交易</span>
      </div>
      <div className="overflow-x-auto">
        <table className="table table-xs text-[13px] text-base-content">
          <thead>
            <tr className="text-[10px] text-base-content/40 uppercase tracking-wider border-b border-base-300">
              <th>时间</th><th>信号</th><th>价格</th><th>数量</th><th>盈亏</th><th>信心</th><th>理由</th>
            </tr>
          </thead>
          <tbody>
            {recent.map(t => (
              <tr key={t.id} className="border-b border-base-300/50 hover:bg-base-100/50">
                <td className="text-base-content/40">{fmtTime(t.timestamp)}</td>
                <td className={`font-bold ${t.signal === 'BUY' ? 'text-success' : t.signal === 'SELL' ? 'text-error' : 'text-warning'}`}>{t.signal}</td>
                <td>${t.price?.toFixed(2) || '—'}</td>
                <td>{t.amount ?? '—'}</td>
                <td>
                  {t.pnl !== 0 ? (
                    <span className={`inline-flex items-center gap-0.5 font-semibold ${t.pnl > 0 ? 'text-success' : 'text-error'}`}>
                      {t.pnl > 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
                      {t.pnl > 0 ? '+' : ''}{t.pnl.toFixed(2)}
                    </span>
                  ) : <span className="text-base-content/40 inline-flex items-center gap-0.5"><Minus className="w-3 h-3" />—</span>}
                </td>
                <td className="text-base-content/40">{t.confidence}</td>
                <td className="max-w-[220px] overflow-hidden text-ellipsis whitespace-nowrap text-base-content/40">
                  {t.reason?.length > 40 ? t.reason.substring(0, 40) + '...' : t.reason || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
