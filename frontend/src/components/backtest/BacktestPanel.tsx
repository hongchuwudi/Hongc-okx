import { useState, useEffect, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import { Play, Loader2, TrendingUp, Target, BarChart3, Activity, AlertTriangle, ChevronRight, History, Plus } from 'lucide-react'

interface BTSummary { id: number; strategy_name: string; symbol: string; timeframe: string; data_count: number; status: string; total_return_pct: number; win_rate: number; profit_factor: number; max_drawdown_pct: number; sharpe_ratio: number; total_trades: number; started_at: string; finished_at: string }
interface BT { ok: boolean; run_id?: number; error?: string; metrics?: BacktestMetrics; trades?: BacktestTrade[]; equity_curve?: EquityPoint[]; id?: number; strategy_name?: string; status?: string; initial_capital?: number; final_equity?: number; total_return_pct?: number; win_rate?: number; profit_factor?: number; max_drawdown_pct?: number; sharpe_ratio?: number; total_trades?: number; winning_trades?: number; losing_trades?: number; avg_trade_pnl?: number; trades_?: BacktestTrade[]; equity_curve_?: EquityPoint[] }
interface BacktestMetrics { initial_capital: number; final_equity: number; total_return_pct: number; total_trades: number; winning_trades: number; losing_trades: number; win_rate: number; profit_factor: number; max_drawdown_pct: number; sharpe_ratio: number; avg_trade_pnl: number }
interface BacktestTrade { bar: number; timestamp: string; side: string; entry: number; exit: number; size: number; pnl: number; bars_held: number; confidence: string }
interface EquityPoint { bar: number; timestamp: string; equity: number }

const API = '/api/backtest'

let _runsCache: BTSummary[] | null = null

export default function BacktestPanel() {
  const [runs, setRuns] = useState<BTSummary[]>(_runsCache || [])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<BT | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [showForm, setShowForm] = useState(false)

  // 策略配置
  const [strategy, setStrategy] = useState('technical')
  const [dataLimit, setDataLimit] = useState(500)
  const [capital, setCapital] = useState(100)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 打开页面自动加载历史列表
  const loadRuns = useCallback(async () => {
    try {
      const r = await fetch(`${API}/runs?limit=20`)
      const data: BTSummary[] = await r.json()
      _runsCache = data
      setRuns(data)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => { loadRuns() }, [loadRuns])

  // 点击一条历史记录加载详情
  async function selectRun(id: number) {
    setSelectedId(id)
    setLoadingDetail(true)
    try {
      const r = await fetch(`${API}/runs/${id}`)
      const d: BT = await r.json()
      setDetail(d.ok ? d : null)
    } catch { setDetail(null) }
    finally { setLoadingDetail(false) }
  }

  // 运行新回测
  async function run() {
    setRunning(true); setError(null)
    try {
      const r = await fetch(`${API}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ strategy, data_limit: dataLimit, initial_capital: capital }) })
      const d: BT = await r.json()
      if (d.ok) {
        setDetail(d); setSelectedId(d.run_id || null)
        loadRuns() // 刷新列表
      } else { setError(d.error || 'error') }
    } catch (e: unknown) { setError(e instanceof Error ? e.message : 'error') }
    finally { setRunning(false) }
  }

  function eqOption(curve: EquityPoint[]): EChartsOption {
    const dark = document.documentElement.dataset.theme === 'dark'
    const t = dark ? '#8a8a9e' : '#6b6b7b'; const t2 = dark ? '#5a5a72' : '#9b9bae'; const b = dark ? '#1f1f3a' : '#e8e8ec'
    return { backgroundColor: 'transparent', grid: { left: 60, right: 16, top: 8, bottom: 24 },
      xAxis: { type: 'category', data: curve.map(p => p.bar), axisLabel: { color: t2, fontSize: 10 }, axisLine: { lineStyle: { color: b } }, axisTick: { show: false } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: b, type: 'dashed' } }, axisLabel: { color: t, fontSize: 11, formatter: (v: number) => '$' + v.toFixed(0) } },
      tooltip: { trigger: 'axis', backgroundColor: dark ? 'rgba(20,20,37,0.95)' : 'rgba(255,255,255,0.95)', borderColor: b, textStyle: { color: t, fontSize: 12 } },
      series: [{ type: 'line', data: curve.map(p => p.equity), smooth: true, symbol: 'none', lineStyle: { color: '#3370FF', width: 2 }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(51,112,255,0.2)' }, { offset: 1, color: 'rgba(0,0,0,0)' }] } } }],
    } as EChartsOption
  }

  return (
    <div className="space-y-4">
      {/* 历史回测列表 */}
      <div className="card-dash bg-base-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <History className="w-[18px] h-[18px] text-primary" />
            <span className="text-[13px] font-semibold text-base-content">回测记录</span>
          </div>
          <button className="btn btn-primary btn-sm btn-outline" onClick={() => { setShowForm(!showForm); setSelectedId(null); setDetail(null) }}>
            <Plus className="w-[14px] h-[14px]" />新回测
          </button>
        </div>

        {/* 新建回测表单 */}
        {showForm && (
          <div className="flex flex-wrap items-end gap-3 mb-3 p-3 rounded-xl bg-base-100/50 border border-base-300">
            <div><label className="text-[11px] text-base-content/40 font-semibold block mb-1">策略</label><select className="select select-sm" value={strategy} onChange={e => setStrategy(e.target.value)}><option value="technical">技术指标</option><option value="deepseek">DeepSeek AI</option></select></div>
            <div><label className="text-[11px] text-base-content/40 font-semibold block mb-1">K线数</label><select className="select select-sm" value={dataLimit} onChange={e => setDataLimit(+e.target.value)}>{[200, 500, 1000, 2000].map(v => <option key={v} value={v}>{v}</option>)}</select></div>
            <div><label className="text-[11px] text-base-content/40 font-semibold block mb-1">初始资金</label><input type="number" className="input input-sm w-28" value={capital} onChange={e => setCapital(+e.target.value)} min={10} /></div>
            <button className="btn btn-primary btn-sm" onClick={run} disabled={running}>{running ? <Loader2 className="w-[18px] h-[18px] animate-spin" /> : <Play className="w-[18px] h-[18px]" />}开始</button>
          </div>
        )}

        {error && <div className="alert alert-error mb-3 py-2"><AlertTriangle className="w-4 h-4" /><span className="text-sm">{error}</span></div>}

        {/* 回测列表 */}
        {runs.length === 0 ? (
          <div className="text-center py-8 text-[13px] text-base-content/40">暂无回测记录，点击"新回测"开始</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table table-xs text-[13px] text-base-content">
              <thead>
                <tr className="text-[10px] text-base-content/40 uppercase tracking-wider border-b border-base-300">
                  <th>ID</th><th>策略</th><th>数据</th><th>收益率</th><th>胜率</th><th>盈亏比</th><th>夏普</th><th>回撤</th><th>状态</th><th></th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id} className={`border-b border-base-300/50 hover:bg-base-100/50 cursor-pointer ${selectedId === r.id ? 'bg-primary/5' : ''}`} onClick={() => selectRun(r.id)}>
                    <td className="text-base-content/40">#{r.id}</td>
                    <td className="font-semibold">{r.strategy_name === 'technical' ? '技术' : 'DeepSeek'}</td>
                    <td className="text-base-content/40">{r.data_count}根</td>
                    <td className={`font-bold ${(r.total_return_pct || 0) >= 0 ? 'text-success' : 'text-error'}`}>{(r.total_return_pct || 0) >= 0 ? '+' : ''}{r.total_return_pct?.toFixed(1)}%</td>
                    <td>{r.win_rate?.toFixed(0)}%</td>
                    <td>{r.profit_factor?.toFixed(2)}</td>
                    <td>{r.sharpe_ratio?.toFixed(1)}</td>
                    <td className="text-error">{r.max_drawdown_pct?.toFixed(1)}%</td>
                    <td><span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${r.status === 'completed' ? 'bg-success/10 text-success' : r.status === 'running' ? 'bg-warning/10 text-warning' : 'bg-error/10 text-error'}`}>{r.status}</span></td>
                    <td><ChevronRight className="w-3 h-3 text-base-content/30" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 选中回测的详情 */}
      {loadingDetail && (
        <div className="card-dash bg-base-200 flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      )}

      {detail && detail.metrics && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <MiniM icon={TrendingUp} label="Total Return" value={`${(detail.metrics.total_return_pct || 0) >= 0 ? '+' : ''}${detail.metrics.total_return_pct}%`} color={(detail.metrics.total_return_pct || 0) >= 0 ? 'text-success' : 'text-error'} />
            <MiniM icon={Target} label="Win Rate" value={`${detail.metrics.win_rate}%`} color="text-primary" />
            <MiniM icon={BarChart3} label="Trades" value={`${detail.metrics.total_trades}`} color="text-base-content" />
            <MiniM icon={Activity} label="Sharpe" value={`${detail.metrics.sharpe_ratio}`} color="text-warning" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <MiniM icon={TrendingUp} label="Final Equity" value={`$${detail.metrics.final_equity}`} color="text-base-content" />
            <MiniM icon={Target} label="Profit Factor" value={`${detail.metrics.profit_factor}`} color="text-success" />
            <MiniM icon={AlertTriangle} label="Max DD" value={`${detail.metrics.max_drawdown_pct}%`} color="text-error" />
            <MiniM icon={Activity} label="Avg PnL" value={`$${detail.metrics.avg_trade_pnl}`} color="text-base-content/60" />
          </div>

          {detail.equity_curve && detail.equity_curve.length > 0 && (
            <div className="card-dash bg-base-200">
              <div className="flex items-center gap-2 mb-1"><TrendingUp className="w-[18px] h-[18px] text-base-content/60" /><span className="text-[13px] font-semibold text-base-content">Equity Curve</span></div>
              <ReactECharts option={eqOption(detail.equity_curve)} style={{ height: 300 }} notMerge />
            </div>
          )}

          {detail.trades && detail.trades.length > 0 && (
            <div className="card-dash bg-base-200">
              <div className="flex items-center gap-2 mb-3"><BarChart3 className="w-[18px] h-[18px] text-base-content/60" /><span className="text-[13px] font-semibold text-base-content">Trades ({detail.trades.length})</span></div>
              <div className="overflow-x-auto">
                <table className="table table-xs text-[13px] text-base-content">
                  <thead><tr className="text-[10px] text-base-content/40 uppercase tracking-wider border-b border-base-300"><th>#</th><th>Side</th><th>Entry</th><th>Exit</th><th>PnL</th><th>Bars</th><th>Type</th></tr></thead>
                  <tbody>
                    {detail.trades.map((t, i) => (
                      <tr key={i} className="border-b border-base-300/50 hover:bg-base-100/50">
                        <td className="text-base-content/40">{i + 1}</td>
                        <td className={t.side === 'long' ? 'text-success font-bold' : 'text-error font-bold'}>{t.side}</td>
                        <td>${t.entry.toFixed(2)}</td><td>${t.exit.toFixed(2)}</td>
                        <td className={`font-semibold ${t.pnl >= 0 ? 'text-success' : 'text-error'}`}>{t.pnl >= 0 ? '+' : ''}{t.pnl.toFixed(4)}</td>
                        <td className="text-base-content/40">{t.bars_held}</td>
                        <td><span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-primary/10 text-primary border border-primary/20">{t.confidence}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function MiniM({ icon: Icon, label, value, color }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string; color: string }) {
  return (
    <div className="card-dash bg-base-200 text-center py-3 px-2">
      <Icon className="w-[16px] h-[16px] mx-auto mb-1 text-base-content/40" />
      <div className="text-[9px] text-base-content/40 font-semibold uppercase tracking-wider mb-1">{label}</div>
      <div className={`text-[16px] font-bold tabular-nums ${color}`}>{value}</div>
    </div>
  )
}
