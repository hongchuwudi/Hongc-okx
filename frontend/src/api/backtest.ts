/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 回测 API — 同步/异步/流式执行 + K线预览 + 历史记录查询
 *
 * 包含:
 * - runBacktest          — 同步回测，阻塞等待完成后返回结果
 * - runBacktestStream    — 流式回测（SSE），逐 K 线推送进度/信号/交易
 * - runBacktestAsync     — 异步回测，立即返回 run_id，WebSocket 推送进度
 * - fetchOhlcvPreview    — 拉取 OHLCV 原始数据预览，确认 K 线数量和走势
 * - fetchBacktestRuns    — 分页查询历史回测运行记录列表
 * - fetchBacktestDetail  — 查询单次回测完整详情（配置/指标/交易/权益曲线）
 */

import { get, post } from '../utils/request'
import type {
  BacktestRunRequest, BacktestRunItem, BacktestDetail,
  BacktestRunResult, BacktestStreamEvent,
} from '../types/backtest'
import type { OhlcvBar } from '../types/kline'

const BASE = '/api/v1'

// ── 回测执行 ──────────────────────────────────────────

// 同步回测 — 提交参数后阻塞等待，完成后返回完整结果
// 适用于数据量较小（< 200 根 K 线）的快速回测
export const runBacktest = (req: BacktestRunRequest) =>
  post<BacktestRunResult>('/backtest/run', req)

// 流式回测 — SSE（Server-Sent Events）逐 K 线推送
// 返回 AsyncGenerator，调用方用 for await...of 消费事件流
// 事件类型: progress（每根 K 线）/ done（完成，含指标和权益曲线）/ error（异常）
export async function* runBacktestStream(req: BacktestRunRequest): AsyncGenerator<BacktestStreamEvent> {
  const res = await fetch(`${BASE}/backtest/run-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })

  if (!res.ok) {
    let msg: string
    try { msg = (await res.json())?.detail || '' } catch { msg = await res.text().catch(() => '') }
    throw new Error(msg || `服务器错误 (${res.status})`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6)) as BacktestStreamEvent
      }
    }
  }
}

// 异步回测 — 提交参数后立即返回 run_id，不阻塞
// 通过 WebSocket 推送进度，适合长时间运行的回测
export const runBacktestAsync = (req: BacktestRunRequest) =>
  post<{ ok: boolean; run_id: number; status: string }>('/backtest/run-async', req)

// ── K 线预览 ──────────────────────────────────────────

// 拉取指定交易对/周期的 OHLCV 原始数据预览
// 返回 { data: OhlcvBar[], count }，用于回测前确认实际拉到的 K 线数量和走势
export const fetchOhlcvPreview = (req: BacktestRunRequest) =>
  post<{ data: OhlcvBar[]; count: number }>('/backtest/preview', req)

// ── 历史记录 ──────────────────────────────────────────

// 分页查询历史回测运行记录列表，按启动时间倒序
// 返回 { data, page, page_size, total, total_pages }
// 每条记录含策略名/交易对/周期/收益率/胜率/最大回撤/夏普比率/状态
export const fetchBacktestRuns = (page = 1, pageSize = 20) =>
  get<{ data: BacktestRunItem[]; page: number; page_size: number; total: number; total_pages: number }>(
    `/backtest/runs?page=${page}&page_size=${pageSize}`
  )

// 查询单次回测完整详情
// 返回 BacktestDetail，含: 配置参数、绩效指标（收益率/胜率/夏普/最大回撤）、
// 交易明细列表（含每笔开平仓方向/价格/盈亏）、权益曲线数据点
export const fetchBacktestDetail = (runId: number) =>
  get<BacktestDetail>(`/backtest/runs/${runId}`)
