/**
 * 创建时间: 2026-06-11
 * 作者: hongchuwudi
 * 描述: 回测 API — 同步/异步/流式执行、历史列表、详情查询
 */

import { get, post } from '../utils/request'
import type { BacktestRunRequest, BacktestRunItem, BacktestDetail, BacktestRunResult, BacktestStreamEvent } from '../types/backtest'
import type { OhlcvBar } from '../types/kline'

const BASE = '/api/v1'

// 同步回测（等待完成）
export const runBacktest = (req: BacktestRunRequest) =>
  post<BacktestRunResult>('/backtest/run', req)

// 流式回测 — SSE 逐 K 线推送，返回 async generator，调用方用 for await 消费
export async function* runBacktestStream(req: BacktestRunRequest): AsyncGenerator<BacktestStreamEvent> {
  const res = await fetch(`${BASE}/backtest/run-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })

  if (!res.ok) {
    let msg = ''
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

// K线预览 — 返回 OHLCV 原始数据，用于确认实际拉到的K线数量和走势
export const fetchOhlcvPreview = (req: BacktestRunRequest) =>
  post<{ data: OhlcvBar[]; count: number }>('/backtest/preview', req)

// 异步回测（立即返回 run_id，WebSocket 推送进度）
export const runBacktestAsync = (req: BacktestRunRequest) =>
  post<{ ok: boolean; run_id: number; status: string }>('/backtest/run-async', req)

// 历史回测运行记录列表，按启动时间倒序，支持分页
export const fetchBacktestRuns = (page = 1, pageSize = 20) =>
  get<{ data: BacktestRunItem[]; page: number; page_size: number; total: number; total_pages: number }>(
    `/backtest/runs?page=${page}&page_size=${pageSize}`
  )

// 单次回测完整详情：含配置参数、绩效指标、交易明细、权益曲线
export const fetchBacktestDetail = (runId: number) =>
  get<BacktestDetail>(`/backtest/runs/${runId}`)
