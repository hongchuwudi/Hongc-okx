/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 历史开单记录页面 — 分页表格 + 盈亏统计摘要
 *
 * 包含:
 * - StatsBar — 顶部统计条（总笔数/总盈亏/胜率/盈亏比）
 * - TradeTable — 分页交易表格
 */

import { useState, useEffect, useCallback } from 'react'
import { fetchTradesPaged } from '@/api/trades'
import type { Trade } from '@/types/trades'

function fmtTs(ts: string): string {
  const d = new Date(ts.includes('Z') || ts.includes('+') ? ts : ts + 'Z')
  const M = String(d.getMonth() + 1).padStart(2, '0')
  const D = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${M}-${D} ${h}:${m}`
}

function fmtP(p: number): string {
  if (p < 1) return p.toFixed(6)
  if (p < 100) return p.toFixed(4)
  return p.toFixed(2)
}

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (p: number) => {
    setLoading(true)
    try {
      const res = await fetchTradesPaged(p, 20)
      setTrades(res.data)
      setTotal(res.total)
      setTotalPages(res.total_pages)
      setPage(res.page)
    } catch { /* */ }
    setLoading(false)
  }, [])

  useEffect(() => { load(1) }, [load])

  // 统计
  const totalPnl = trades.reduce((s, t) => s + t.pnl, 0)
  const wins = trades.filter(t => t.pnl > 0).length
  const losses = trades.filter(t => t.pnl < 0).length
  const winRate = wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : '--'

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] px-4 py-3">
      {/* 统计条 */}
      <div className="flex items-center gap-6 mb-3 bg-base-100 rounded-lg px-4 py-2.5 border border-base-300 shrink-0">
        <StatItem label="总笔数" value={total.toString()} />
        <StatItem label="总盈亏" value={`${totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)} USDT`} ok={totalPnl >= 0} />
        <StatItem label="胜率" value={`${winRate}%`} />
        <StatItem label="当前页" value={`${wins}赢 / ${losses}亏`} />
      </div>

      {/* 表格 */}
      <div className="flex-1 overflow-auto bg-base-100 rounded-lg border border-base-300">
        <table className="table table-xs table-zebra">
          <thead className="sticky top-0 bg-base-200 z-10">
            <tr>
              <th className="text-[11px]">时间</th>
              <th className="text-[11px]">方向</th>
              <th className="text-[11px] text-right">价格</th>
              <th className="text-[11px] text-right">数量</th>
              <th className="text-[11px] text-right">盈亏</th>
              <th className="text-[11px]">信心</th>
              <th className="text-[11px] w-full">理由</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 && !loading && (
              <tr><td colSpan={7} className="text-center text-base-content/30 py-8">暂无交易记录</td></tr>
            )}
            {trades.map(t => (
              <tr key={t.id} className="hover:bg-base-200">
                <td className="text-[11px] font-mono text-base-content/50 whitespace-nowrap">{fmtTs(t.timestamp)}</td>
                <td>
                  <span className={`badge badge-xs font-bold ${t.signal === 'BUY' ? 'badge-success' : 'badge-error'}`}>
                    {t.signal}
                  </span>
                </td>
                <td className="text-[11px] font-mono text-right">{fmtP(t.price)}</td>
                <td className="text-[11px] font-mono text-right">{t.amount}</td>
                <td className={`text-[11px] font-mono text-right font-semibold ${t.pnl >= 0 ? 'text-success' : 'text-error'}`}>
                  {t.pnl >= 0 ? '+' : ''}{t.pnl.toFixed(2)}
                </td>
                <td className="text-[11px] text-base-content/50">{t.confidence}</td>
                <td className="text-[11px] text-base-content/50 truncate max-w-xs">{t.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="flex items-center justify-center gap-2 py-2 shrink-0">
        <button className="btn btn-xs btn-ghost" disabled={page <= 1} onClick={() => load(page - 1)}>上一页</button>
        <span className="text-xs text-base-content/40">{page} / {totalPages}</span>
        <button className="btn btn-xs btn-ghost" disabled={page >= totalPages} onClick={() => load(page + 1)}>下一页</button>
      </div>
    </div>
  )
}

function StatItem({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[10px] text-base-content/40">{label}</span>
      <span className={`text-xs font-semibold font-mono ${ok === undefined ? '' : ok ? 'text-success' : 'text-error'}`}>
        {value}
      </span>
    </div>
  )
}
