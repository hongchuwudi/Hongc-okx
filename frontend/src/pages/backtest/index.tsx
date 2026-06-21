/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测页面 — 左侧参数面板 + 右侧结果/历史
 *
 * 该组件实现了一个完整的策略回测界面，包含：
 * 1. 左侧边栏 - 回测参数配置表单，支持两种策略（技术指标 / DeepSeek AI）
 * 2. 右侧主区域 - 根据当前视图切换显示回测结果或历史记录
 * 3. SSE 流式回测 - 逐K线推送进度，实时渲染权益曲线和交易记录
 * 4. 自动轮询 - 每10秒刷新历史记录列表
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { Info, Play, Square, CandlestickChart } from 'lucide-react'
import { runBacktestStream, fetchBacktestRuns, fetchBacktestDetail, fetchOhlcvPreview } from '@/api/backtest'
import type { BacktestRunRequest, BacktestRunItem, BacktestDetail, BacktestTrade } from '@/types/backtest'
import type { OhlcvBar } from '@/types/kline'
import { SelectField } from './components/BacktestFormFields'
import ResultCards from './components/ResultCards'
import ChartCard from './components/ChartCard'
import KlineChart from './components/KlineChart'
import TradeTable from './components/TradeTable'
import RunsTable from './components/RunsTable'
import ParamDrawer from './components/ParamDrawer'
import { STRATEGIES, SYMBOLS, TIMEFRAMES, CAPITALS, POSITION_RATIOS, FEE_RATES, WARMUPS, DATA_LIMITS, TEMPERATURES } from '@/constants/backtest'

const DEFAULT_FORM: BacktestRunRequest = {
  strategy: 'technical',
  symbol: 'DOGE/USDT:USDT',
  timeframe: '5m',
  initial_capital: 15,
  position_ratio: 0.5,
  fee_rate: 0.0010,
  warmup: 20,
  data_limit: 500,
  temperature: 0.1,
}

type View = 'result' | 'history'

export default function Backtest() {
  // ====== 状态管理 ======
  const [view, setView] = useState<View>('result')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<BacktestRunRequest>(DEFAULT_FORM)

  // 流式进度
  const [streamBar, setStreamBar] = useState(0)
  const [streamTotal, setStreamTotal] = useState(0)
  const [streamSignal, setStreamSignal] = useState('—')
  const [streamConfidence, setStreamConfidence] = useState('')
  const [streamPosition, setStreamPosition] = useState<string | null>(null)

  // 流式累积数据
  const [streamEquity, setStreamEquity] = useState<{ timestamp: number; equity: number }[]>([])
  const [streamTrades, setStreamTrades] = useState<BacktestTrade[]>([])
  const [streamMetrics, setStreamMetrics] = useState<Record<string, number> | null>(null)
  const [streamDone, setStreamDone] = useState(false)

  // K线预览
  const [previewData, setPreviewData] = useState<OhlcvBar[]>([])
  const [previewCount, setPreviewCount] = useState(0)
  const [previewLoading, setPreviewLoading] = useState(false)

  // 历史记录
  const [runs, setRuns] = useState<BacktestRunItem[]>([])
  const [runsPage, setRunsPage] = useState(1)
  const [runsPageSize, setRunsPageSize] = useState(20)
  const [runsTotal, setRunsTotal] = useState(0)
  const [runsPages, setRunsPages] = useState(1)
  const [detail, setDetail] = useState<BacktestDetail | null>(null)
  const runsTimerRef = useRef<ReturnType<typeof setInterval>>()
  const abortRef = useRef<AbortController | null>(null)

  const setField = useCallback((key: keyof BacktestRunRequest, value: string | number) => {
    setForm(prev => ({ ...prev, [key]: value }))
  }, [])

  const loadRuns = useCallback(async (page = 1, pageSize = 20) => {
    try {
      const res = await fetchBacktestRuns(page, pageSize)
      setRuns(res.data)
      setRunsPage(res.page)
      setRunsPageSize(res.page_size)
      setRunsTotal(res.total)
      setRunsPages(res.total_pages)
    } catch { /* 静默 */ }
  }, [])

  // 核心：流式回测 — 逐K线消费 SSE 事件
  const handleRun = useCallback(async () => {
    abortRef.current?.abort()
    const ac = new AbortController()
    abortRef.current = ac

    setRunning(true)
    setError(null)
    setStreamBar(0)
    setStreamTotal(0)
    setStreamSignal('—')
    setStreamConfidence('')
    setStreamPosition(null)
    setStreamEquity([])
    setStreamTrades([])
    setStreamMetrics(null)
    setStreamDone(false)

    try {
      for await (const event of runBacktestStream(form)) {
        if (ac.signal.aborted) break

        switch (event.type) {
          case 'progress': {
            setStreamBar(event.bar)
            setStreamTotal(event.total)
            setStreamSignal(event.signal)
            setStreamConfidence(event.confidence)
            setStreamPosition(event.position_side)
            setStreamEquity(prev => [...prev, { timestamp: event.timestamp, equity: event.equity }])
            if (event.trade) {
              setStreamTrades(prev => [...prev, event.trade!])
            }
            break
          }
          case 'done': {
            if (event.equity_curve) {
              setStreamMetrics(event.metrics)
              setStreamEquity(event.equity_curve)
              setStreamTrades(event.trades)
            }
            setStreamDone(true)
            setRunning(false)
            loadRuns(1)
            if (previewData.length === 0) {
              fetchOhlcvPreview(form).then(res => {
                setPreviewData(res.data)
                setPreviewCount(res.count)
              }).catch(() => {})
            }
            break
          }
          case 'error': {
            setError(event.message)
            setRunning(false)
            break
          }
        }
      }
    } catch (err: unknown) {
      if (!ac.signal.aborted) {
        setError(err instanceof Error ? err.message : '流式回测中断')
        setRunning(false)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- previewData.length 变化不应重建此回调
  }, [form, loadRuns])

  // 取消回测
  const handleCancel = useCallback(() => {
    abortRef.current?.abort()
    setRunning(false)
  }, [])

  // 预览K线 — 拉取实际 OHLCV 数据展示蜡烛图
  const handlePreview = async () => {
    setPreviewLoading(true)
    setPreviewData([])
    try {
      const res = await fetchOhlcvPreview(form)
      setPreviewData(res.data)
      setPreviewCount(res.count)
    } catch {
      setPreviewCount(0)
    } finally {
      setPreviewLoading(false)
    }
  }

  const viewDetail = useCallback(async (runId: number) => {
    setView('history')
    setError(null)
    try {
      const data = await fetchBacktestDetail(runId)
      setDetail(data)
      // 同时拉取 OHLCV 数据，用于 K 线图上标记交易点位
      fetchOhlcvPreview({
        strategy: data.strategy_name,
        symbol: data.symbol,
        timeframe: data.timeframe,
        initial_capital: data.initial_capital,
        position_ratio: 0.5,
        fee_rate: 0.001,
        warmup: data.warmup,
        data_limit: data.data_count,
        temperature: 0.1,
      }).then(res => {
        setPreviewData(res.data)
        setPreviewCount(res.count)
      }).catch(() => {})
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '加载详情失败')
    }
  }, [])

  // ====== 副作用 ======
  useEffect(() => { loadRuns() }, [loadRuns])

  useEffect(() => {
    runsTimerRef.current = setInterval(loadRuns, 10000)
    return () => clearInterval(runsTimerRef.current)
  }, [loadRuns])

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  // 权益曲线 ECharts 配置 — 优先流式数据，其次历史详情
  const equityOption = (() => {
    const raw = detail?.equity_curve || (streamEquity?.length ? streamEquity : [])
    if (raw.length === 0) return {}

    // 降采样
    const maxPoints = 300
    const step = raw.length > maxPoints ? Math.ceil(raw.length / maxPoints) : 1
    const curve = step > 1 ? raw.filter((_, i) => i % step === 0) : raw

    // 用 bar index 做 x 轴，避免 time 轴的任何排序/解析问题
    const data = curve.map((p: { timestamp: number; equity: number }, i: number) => [i, p.equity] as [number, number])
    const tsMin = curve.length > 0 ? curve[0].timestamp : 0
    const tsMax = curve.length > 0 ? curve[curve.length - 1].timestamp : 0
    const spanMs = tsMax - tsMin

    return {
      grid: { top: 20, right: 20, bottom: 30, left: 60 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: {
          fontSize: 11,
          formatter: (v: number) => {
            const idx = Math.round(v)
            const ts = curve[idx]?.timestamp
            if (!ts) return ''
            const d = new Date(ts)
            if (spanMs < 3600_000) return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
            if (spanMs < 86400_000) return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
            return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
          },
        },
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: { fontSize: 11 },
      },
      series: [{
        data,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#1772F6', width: 2 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(23,114,246,0.15)' },
              { offset: 1, color: 'rgba(23,114,246,0.02)' }
            ]
          }
        },
      }],
      tooltip: {
        trigger: 'axis',
        formatter: (params: { value: [number, number] }[]) => {
          const p = params[0]?.value
          if (!p) return ''
          const idx = Math.round(p[0])
          const ts = curve[idx]?.timestamp
          return `${ts ? new Date(ts).toLocaleString() : ''}<br/>权益: $${p[1].toFixed(2)}`
        },
      },
    }
  })()

  // ====== 渲染 ======
  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:h-[calc(100vh-5rem)]">
      {/* ===== 左侧：参数面板 ===== */}
      <div className="lg:w-64 lg:shrink-0 flex flex-col gap-3 h-full">
        {/* 参数卡片 */}
        <div className="card bg-base-100 border border-base-300 flex-1">
          <div className="card-body p-4 space-y-3 overflow-y-auto">
            <h2 className="card-title text-base">
              回测参数
              <button onClick={() => setDrawerOpen(true)} className="btn btn-ghost btn-xs btn-circle ml-auto">
                <Info className="w-4 h-4" />
              </button>
            </h2>

            <SelectField label="策略" field="strategy" value={form.strategy} options={STRATEGIES} onChange={setField} />
            <SelectField label="交易对" field="symbol" value={form.symbol} options={SYMBOLS} onChange={setField} />
            <SelectField label="K 线周期" field="timeframe" value={form.timeframe} options={TIMEFRAMES} onChange={setField} />
            <SelectField label="初始资金" field="initial_capital"
              value={String(form.initial_capital)} options={CAPITALS}
              onChange={(k, v) => setField(k, Number(v))} />
            <SelectField label="仓位比例" field="position_ratio"
              value={String(form.position_ratio)} options={POSITION_RATIOS}
              onChange={(k, v) => setField(k, Number(v))} />
            <SelectField label="手续费率" field="fee_rate"
              value={String(form.fee_rate)} options={FEE_RATES}
              onChange={(k, v) => setField(k, Number(v))} />
            <SelectField label="预热期" field="warmup"
              value={String(form.warmup)} options={WARMUPS}
              onChange={(k, v) => setField(k, Number(v))} />
            <SelectField label="数据量" field="data_limit"
              value={String(form.data_limit)} options={DATA_LIMITS}
              onChange={(k, v) => setField(k, Number(v))} />

            {form.strategy === 'deepseek' && (
              <>
                <SelectField label="AI 激进度" field="temperature"
                  value={String(form.temperature)} options={TEMPERATURES}
                  onChange={(k, v) => setField(k, Number(v))} />
                <div className="text-xs text-warning bg-warning/5 rounded p-2">
                  AI 回测约需 1-2 分钟，数据量自动限制为 500 条
                </div>
              </>
            )}
          </div>
        </div>

        {/* 操作卡片 */}
        <div className="card bg-base-100 border border-base-300 shrink-0">
          <div className="card-body p-3 space-y-2">
            {running ? (
              <button onClick={handleCancel} className="btn btn-error btn-sm w-full gap-1">
                <Square size={14} /> 取消回测
              </button>
            ) : (
              <div className="flex gap-2">
                <button onClick={handleRun} className="btn btn-primary btn-sm flex-1 gap-1">
                  <Play size={14} /> 开始回测
                </button>
                <button onClick={handlePreview} disabled={previewLoading} className="btn btn-outline btn-sm gap-1">
                  {previewLoading ? <span className="loading loading-spinner loading-xs" /> : <><CandlestickChart size={14} /> 预览K线</>}
                </button>
              </div>
            )}

            <div className="divider text-xs text-base-content/40 my-0">视图</div>

            <div className="flex gap-1">
              <button
                onClick={() => setView('result')}
                className={`btn btn-xs flex-1 ${view === 'result' ? 'btn-primary' : 'btn-ghost'}`}
              >结果</button>
              <button
                onClick={() => { setView('history'); setDetail(null) }}
                className={`btn btn-xs flex-1 ${view === 'history' ? 'btn-primary' : 'btn-ghost'}`}
              >历史</button>
            </div>
          </div>
        </div>
      </div>

      {/* ===== 右侧：结果/历史显示区 ===== */}
      <div className="flex-1 min-w-0 space-y-4 overflow-y-auto">
        {error && (
          <div className="alert alert-error alert-soft text-sm">{error}</div>
        )}

        {view === 'result' && (
          <>
            {/* 流式进度条 */}
            {running && streamTotal > 0 && (
              <div className="card bg-base-100 border border-base-300">
                <div className="card-body p-4 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span className="loading loading-spinner loading-xs" />
                      回测中… K线 {streamBar}/{streamTotal}
                    </span>
                    <span className="text-base-content/60">
                      信号: <span className={`font-mono font-semibold ${
                        streamSignal === 'BUY' ? 'text-success' : streamSignal === 'SELL' ? 'text-error' : 'text-base-content/60'
                      }`}>{streamSignal}</span>
                      <span className="mx-1">|</span>
                      置信度: {streamConfidence}
                      <span className="mx-1">|</span>
                      持仓: {streamPosition === 'long' ? '多头' : streamPosition === 'short' ? '空头' : '空仓'}
                    </span>
                  </div>
                  <progress className="progress progress-primary w-full" value={streamBar} max={streamTotal} />
                </div>
              </div>
            )}

            {/* 完成后的指标卡片 */}
            {streamDone && streamMetrics && (
              <ResultCards metrics={streamMetrics} symbol={form.symbol} />
            )}

            {/* K线图 + 交易标记 — 回测完成后显示在指标和权益曲线之间 */}
            {streamDone && previewData.length > 0 && (
              <div className="card bg-base-100 border border-base-300">
                <div className="card-body p-4">
                  <h2 className="card-title text-base">
                    K线回放 — {form.symbol}·{form.timeframe}（{previewCount} 条）· {streamTrades.length} 笔交易
                  </h2>
                  <div className="flex items-center gap-4 text-xs text-base-content/60 mb-2">
                    <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-green-600" /> 开多</span>
                    <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-red-600" /> 开空</span>
                    <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-amber-500" /> 平仓</span>
                  </div>
                  <KlineChart data={previewData} trades={streamTrades} />
                </div>
              </div>
            )}

            {/* K线预览 — 回测前的数据预览 */}
            {!streamDone && previewData.length > 0 && (
              <div className="card bg-base-100 border border-base-300">
                <div className="card-body p-4">
                  <h2 className="card-title text-base">
                    数据预览 — {form.symbol}·{form.timeframe}（{previewCount} 根 K 线）
                  </h2>
                  <KlineChart data={previewData} />
                </div>
              </div>
            )}

            {/* 权益曲线 — 流式实时更新 */}
            {streamEquity.length > 0 && (
              <ChartCard
                key={streamDone ? 'done' : 'streaming'}
                title={`权益曲线 — ${form.strategy}·${form.symbol}·${form.timeframe}${running ? ' (实时)' : ''}`}
                option={equityOption}
              />
            )}

            {/* 交易明细 — 流式实时更新 */}
            {streamTrades.length > 0 && <TradeTable trades={streamTrades} />}

            {/* 空状态引导 */}
            {!running && streamEquity.length === 0 && previewData.length === 0 && (
              <div className="flex items-center justify-center text-base-content/40 py-20">
                配置左侧参数，点击「开始回测」
              </div>
            )}
          </>
        )}

        {view === 'history' && (
          <>
            {!detail && (
              <div className="card bg-base-100 border border-base-300 h-full">
                <div className="card-body p-4 flex flex-col min-h-0">
                  <h2 className="card-title text-base shrink-0">历史回测记录</h2>
                  <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                    <RunsTable
                      runs={runs}
                      onView={viewDetail}
                      page={runsPage}
                      pageSize={runsPageSize}
                      totalPages={runsPages}
                      total={runsTotal}
                      onPageChange={loadRuns}
                    />
                  </div>
                </div>
              </div>
            )}
            {detail && (
              <>
                <div className="flex items-center gap-2">
                  <button onClick={() => setDetail(null)} className="btn btn-sm btn-ghost">← 返回列表</button>
                  <span className="text-sm text-base-content/60">#{detail.id} · {detail.strategy_name} · {detail.symbol}</span>
                </div>
                <ResultCards metrics={{
                  total_return_pct: detail.total_return_pct, win_rate: detail.win_rate,
                  sharpe_ratio: detail.sharpe_ratio, max_drawdown_pct: detail.max_drawdown_pct,
                  profit_factor: detail.profit_factor, total_trades: detail.total_trades,
                  final_equity: detail.final_equity, winning_trades: detail.winning_trades,
                  losing_trades: detail.losing_trades, avg_trade_pnl: detail.avg_trade_pnl,
                } as Record<string, number>} symbol={detail.symbol} />

                {/* K线图 + 交易标记 — 历史回测详情 */}
                {previewData.length > 0 && (
                  <div className="card bg-base-100 border border-base-300">
                    <div className="card-body p-4">
                      <h2 className="card-title text-base">
                        K线回放 — {detail.symbol}·{detail.timeframe}（{previewCount} 条）· {detail.trades.length} 笔交易
                      </h2>
                      <div className="flex items-center gap-4 text-xs text-base-content/60 mb-2">
                        <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-green-600" /> 开多</span>
                        <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-red-600" /> 开空</span>
                        <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-amber-500" /> 平仓</span>
                      </div>
                      <KlineChart data={previewData} trades={detail.trades} />
                    </div>
                  </div>
                )}

                <ChartCard title={`权益曲线 — ${detail.strategy_name}·${detail.symbol}`} option={equityOption} />
                <TradeTable trades={detail.trades} />
              </>
            )}
          </>
        )}
      </div>

      <ParamDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  )
}
