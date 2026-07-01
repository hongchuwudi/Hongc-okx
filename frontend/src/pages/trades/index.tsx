/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 交易记录页面 — OKX 真实成交 + 系统记录，分页/筛选/统计
 *
 * 包含:
 * - 数据源切换 — OKX 成交 | 系统记录
 * - OKX 表格 — 订单ID/成交ID/方向/价格/数量/成交额/手续费/角色/类型
 * - 系统表格 — 时间/方向/价格/数量/盈亏/信心/理由
 * - 底部分页 — Paginator 统一分页
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { fetchTradesPaged, fetchOkxTrades } from '@/api/trades'
import type { Trade, OkxTrade } from '@/types/trades'
import Paginator from '@/components/common/Paginator'
import FormSelect from '@/components/common/FormSelect'
import { Hash, DollarSign, Target, RefreshCw, Database, Link, Filter } from 'lucide-react'

type DataSource = 'okx' | 'system'

function fmtTs(ts: string): string {
  if (!ts) return '--'
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
  const [source, setSource] = useState<DataSource>('okx')

  // OKX 状态
  const [okxData, setOkxData] = useState<OkxTrade[]>([])
  const [okxPage, setOkxPage] = useState(1)
  const [okxPageSize, setOkxPageSize] = useState(20)
  const [okxTotal, setOkxTotal] = useState(0)
  const [okxLoading, setOkxLoading] = useState(false)
  const [okxSide, setOkxSide] = useState<'buy' | 'sell' | ''>('')

  // 系统状态
  const [sysData, setSysData] = useState<Trade[]>([])
  const [sysPage, setSysPage] = useState(1)
  const [sysPageSize, setSysPageSize] = useState(20)
  const [sysTotal, setSysTotal] = useState(0)
  const [sysLoading, setSysLoading] = useState(false)

  // ---- OKX 加载 ----
  const loadOkx = useCallback(async (p: number, ps: number, s: string) => {
    setOkxLoading(true)
    try {
      const res = await fetchOkxTrades({
        page: p, pageSize: ps,
        side: (s || undefined) as 'buy' | 'sell' | undefined,
      })
      setOkxData(res.data)
      setOkxTotal(res.total)
      setOkxPage(res.page)
    } catch { /* */ }
    setOkxLoading(false)
  }, [])

  useEffect(() => { if (source === 'okx') loadOkx(1, okxPageSize, okxSide) }, [source, okxPageSize, okxSide, loadOkx])

  // ---- 系统加载 ----
  const loadSys = useCallback(async (p: number, ps: number) => {
    setSysLoading(true)
    try {
      const res = await fetchTradesPaged(p, ps)
      setSysData(res.data)
      setSysTotal(res.total)
      setSysPage(res.page)
    } catch { /* */ }
    setSysLoading(false)
  }, [])

  useEffect(() => { if (source === 'system') loadSys(1, sysPageSize) }, [source, sysPageSize, loadSys])

  // ---- 统计 ----
  const okxStats = useMemo(() => {
    const buys = okxData.filter(t => t.side === 'BUY').length
    const sells = okxData.filter(t => t.side === 'SELL').length
    const vol = okxData.reduce((s, t) => s + t.cost, 0)
    const fee = okxData.reduce((s, t) => s + t.fee, 0)
    return { buys, sells, vol, fee }
  }, [okxData])

  const sysStats = useMemo(() => {
    const pnl = sysData.reduce((s, t) => s + t.pnl, 0)
    const wins = sysData.filter(t => t.pnl > 0).length
    const losses = sysData.filter(t => t.pnl < 0).length
    const wr = wins + losses > 0 ? ((wins / (wins + losses)) * 100).toFixed(1) : '--'
    return { pnl, wins, losses, wr }
  }, [sysData])

  const isOkx = source === 'okx'
  const loading = isOkx ? okxLoading : sysLoading
  const td = 'text-xs py-1.5'

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] px-4 pt-3">
      {/* 顶部栏 */}
      <div className="flex items-center gap-4 mb-3 bg-base-100 rounded-lg px-4 py-2.5 border border-base-300 shrink-0 flex-wrap">
        {/* 数据源 */}
        <div className="join">
          <button onClick={() => setSource('okx')} className={`btn btn-xs join-item gap-1 ${isOkx ? 'btn-primary' : 'btn-ghost'}`}>
            <Link size={12} /> OKX 成交
          </button>
          <button onClick={() => setSource('system')} className={`btn btn-xs join-item gap-1 ${!isOkx ? 'btn-primary' : 'btn-ghost'}`}>
            <Database size={12} /> 系统记录
          </button>
        </div>

        <span className="text-base-content/20">|</span>

        {isOkx ? (
          <>
            {/* 方向筛选 */}
            <div className="flex items-center gap-1">
              <Filter size={12} className="text-base-content/40" />
              <FormSelect
                size="xs"
                value={okxSide}
                onChange={v => { setOkxSide(v as typeof okxSide); setOkxPage(1) }}
                options={[
                  { label: '全部方向', value: '' },
                  { label: '买入', value: 'buy' },
                  { label: '卖出', value: 'sell' },
                ]}
              />
            </div>
            <span className="text-base-content/20">|</span>
            <Stat label="总笔数" value={okxTotal.toString()} icon={<Hash size={14} />} />
            <Stat label="买/卖" value={`${okxStats.buys} / ${okxStats.sells}`} icon={<Target size={14} />} />
            <Stat label="当前页成交额" value={`${okxStats.vol.toFixed(2)} USDT`} icon={<DollarSign size={14} />} />
            <Stat label="手续费" value={`${okxStats.fee.toFixed(4)} USDT`} />
          </>
        ) : (
          <>
            <Stat label="总笔数" value={sysTotal.toString()} icon={<Hash size={14} />} />
            <Stat label="总盈亏" value={`${sysStats.pnl >= 0 ? '+' : ''}${sysStats.pnl.toFixed(2)} USDT`} ok={sysStats.pnl >= 0} icon={<DollarSign size={14} />} />
            <Stat label="胜率" value={`${sysStats.wr}%`} icon={<Target size={14} />} />
            <Stat label="当前页" value={`${sysStats.wins}赢 / ${sysStats.losses}亏`} />
          </>
        )}

        <button
          onClick={() => isOkx ? loadOkx(okxPage, okxPageSize, okxSide) : loadSys(sysPage, sysPageSize)}
          className="btn btn-xs btn-ghost gap-1 ml-auto"
          disabled={loading}
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* 表格 */}
      <div className="flex-1 overflow-auto bg-base-100 rounded-lg border border-base-300">
        <table className="table table-sm table-zebra table-fixed w-full">
          <thead className="sticky top-0 bg-base-200 z-10">
            {isOkx ? (
              <tr>
                <th className="text-xs w-[8%]">时间</th>
                <th className="text-xs w-[5%]">方向</th>
                <th className="text-xs text-right w-[8%]">价格</th>
                <th className="text-xs text-right w-[6%]">数量</th>
                <th className="text-xs text-right w-[8%]">成交额</th>
                <th className="text-xs text-right w-[7%]">盈亏</th>
                <th className="text-xs text-right w-[7%]">手续费</th>
                <th className="text-xs w-[5%]">角色</th>
                <th className="text-xs w-[5%]">类型</th>
                <th className="text-xs text-right w-[8%]">订单ID</th>
                <th className="text-xs text-right w-full">成交ID</th>
              </tr>
            ) : (
              <tr>
                <th className="text-xs w-[8%]">时间</th>
                <th className="text-xs w-[5%]">方向</th>
                <th className="text-xs text-right w-[8%]">价格</th>
                <th className="text-xs text-right w-[6%]">数量</th>
                <th className="text-xs text-right w-[8%]">盈亏</th>
                <th className="text-xs w-[6%]">信心</th>
                <th className="text-xs w-full">理由</th>
              </tr>
            )}
          </thead>
          <tbody>
            {isOkx ? (
              okxData.length === 0 && !loading ? (
                <tr><td colSpan={11} className="text-center text-base-content/30 py-8">暂无 OKX 成交记录</td></tr>
              ) : (
                okxData.map(t => (
                  <tr key={`${t.id}-${t.order_id}`} className="hover:bg-base-200">
                    <td className={`${td} font-mono text-base-content/50 whitespace-nowrap`}>{fmtTs(t.timestamp)}</td>
                    <td className={td}>
                      <span className={`badge badge-xs font-bold ${t.side === 'BUY' ? 'badge-success' : 'badge-error'}`}>
                        {t.side}
                      </span>
                    </td>
                    <td className={`${td} font-mono text-right`}>{fmtP(t.price)}</td>
                    <td className={`${td} font-mono text-right`}>{t.amount}</td>
                    <td className={`${td} font-mono text-right`}>{t.cost.toFixed(2)}</td>
                    <td className={`${td} font-mono text-right font-semibold ${t.pnl > 0 ? 'text-success' : t.pnl < 0 ? 'text-error' : 'text-base-content/50'}`}>
                      {t.pnl !== 0 ? `${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(4)}` : '--'}
                    </td>
                    <td className={`${td} font-mono text-right text-base-content/50`}>
                      {t.fee > 0 ? `${t.fee.toFixed(4)}` : '--'}
                    </td>
                    <td className={`${td} text-base-content/50 capitalize`}>{t.role || '--'}</td>
                    <td className={`${td} text-base-content/50`}>{t.type || '--'}</td>
                    <td className={`${td} font-mono text-[10px] text-base-content/40 truncate`} title={t.order_id}>
                      {t.order_id ? `...${t.order_id.slice(-8)}` : '--'}
                    </td>
                    <td className={`${td} font-mono text-[10px] text-base-content/40 truncate`} title={t.id}>
                      {t.id ? `...${t.id.slice(-8)}` : '--'}
                    </td>
                  </tr>
                ))
              )
            ) : (
              sysData.length === 0 && !loading ? (
                <tr><td colSpan={7} className="text-center text-base-content/30 py-8">暂无交易记录</td></tr>
              ) : (
                sysData.map(t => (
                  <tr key={t.id} className="hover:bg-base-200">
                    <td className={`${td} font-mono text-base-content/50 whitespace-nowrap`}>{fmtTs(t.timestamp)}</td>
                    <td className={td}>
                      <span className={`badge badge-xs font-bold ${t.signal === 'BUY' ? 'badge-success' : 'badge-error'}`}>
                        {t.signal}
                      </span>
                    </td>
                    <td className={`${td} font-mono text-right`}>{fmtP(t.price)}</td>
                    <td className={`${td} font-mono text-right`}>{t.amount}</td>
                    <td className={`${td} font-mono text-right font-semibold ${t.pnl >= 0 ? 'text-success' : 'text-error'}`}>
                      {t.pnl >= 0 ? '+' : ''}{t.pnl.toFixed(2)}
                    </td>
                    <td className={`${td} text-base-content/50`}>{t.confidence}</td>
                    <td className={`${td} text-base-content/50 truncate max-w-xs`}>{t.reason}</td>
                  </tr>
                ))
              )
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="flex items-center justify-center py-2 shrink-0">
        {isOkx ? (
          <Paginator
            size="small"
            current={okxPage}
            total={okxTotal}
            pageSize={okxPageSize}
            pageSizeOptions={[10, 20, 50]}
            showSizeChanger
            onChange={(p, ps) => { setOkxPageSize(ps); loadOkx(p, ps, okxSide) }}
          />
        ) : (
          <Paginator
            size="small"
            current={sysPage}
            total={sysTotal}
            pageSize={sysPageSize}
            pageSizeOptions={[10, 20, 50]}
            showSizeChanger
            onChange={(p, ps) => { setSysPageSize(ps); loadSys(p, ps) }}
          />
        )}
      </div>
    </div>
  )
}

function Stat({ icon, label, value, ok }: {
  icon?: React.ReactNode; label: string; value: string; ok?: boolean
}) {
  return (
    <div className="flex items-center gap-1.5">
      {icon && <span className="text-base-content/40">{icon}</span>}
      <span className="text-[10px] text-base-content/40">{label}</span>
      <span className={`text-xs font-semibold font-mono ${ok === undefined ? '' : ok ? 'text-success' : 'text-error'}`}>
        {value}
      </span>
    </div>
  )
}
