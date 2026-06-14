/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: 仪表盘顶栏 — 引擎 / WS / 策略 / 持仓 / 报价 / 主题（单行）
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchEngineStatus, startEngine, stopEngine, resetCircuit } from '@/api/dashboard'

import type { StatusBarProps } from '@/types/props/props'
import { MODE_LABEL } from '@/constants/agent'

function modeName(mode: string) {
  return MODE_LABEL[mode] || mode
}

export default function StatusBar({ agentMode, market, position, wsConnected }: StatusBarProps) {
  const [engineRunning, setEngineRunning] = useState(false)
  const [toggling, setToggling] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [now, setNow] = useState(new Date())
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refreshEngine = useCallback(async () => {
    try { setEngineRunning((await fetchEngineStatus()).running) } catch { /* */ }
  }, [])

  useEffect(() => { refreshEngine() }, [refreshEngine])

  useEffect(() => {
    pollRef.current = setInterval(refreshEngine, 5_000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [refreshEngine])

  // 实时时钟
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const handleStart = useCallback(async () => {
    setToggling(true)
    try { await startEngine(); setEngineRunning(true) } catch { /* */ }
    setToggling(false)
  }, [])

  const handleStop = useCallback(async () => {
    setToggling(true)
    try { await stopEngine(); setEngineRunning(false) } catch { /* */ }
    setToggling(false)
  }, [])

  const handleReset = useCallback(async () => {
    setResetting(true)
    try { await resetCircuit() } catch { /* */ }
    setResetting(false)
  }, [])

  return (
    <div className="flex items-center justify-between bg-base-100 border-b border-base-300 px-3 py-1.5 text-xs">
      {/* 左侧：状态信息 — 每项 shrink-0 + whitespace-nowrap 防止换行 */}
      <div className="flex items-center gap-3">
        {/* 引擎 */}
        <div className="flex items-center gap-1.5 shrink-0 whitespace-nowrap">
          <span className={`w-1.5 h-1.5 rounded-full ${engineRunning ? 'bg-success animate-pulse' : 'bg-base-300'}`} />
          <span className="text-base-content/50">引擎</span>
          <span className={engineRunning ? 'text-success font-semibold' : ''}>{engineRunning ? '运行' : '停止'}</span>
          <button
            onClick={engineRunning ? handleStop : handleStart}
            disabled={toggling}
            className={`btn btn-xs ${engineRunning ? 'btn-ghost text-error' : 'btn-primary'}`}
          >
            {toggling ? '…' : engineRunning ? '停' : '启'}
          </button>
          <button
            onClick={handleReset}
            disabled={resetting}
            className="btn btn-xs btn-ghost text-warning"
            title="重置熔断状态"
          >
            {resetting ? '…' : '重置'}
          </button>
        </div>

        <span className="text-base-content/20">|</span>

        {/* WS 连接 */}
        <div className="flex items-center gap-1.5 shrink-0 whitespace-nowrap">
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-info' : 'bg-error'}`} />
          <span className="text-base-content/50">WS</span>
          <span className={wsConnected ? 'text-info' : 'text-error'}>{wsConnected ? '已连接' : '断开'}</span>
        </div>

        <span className="text-base-content/20">|</span>

        {/* 策略 */}
        <span className="shrink-0 whitespace-nowrap">{modeName(agentMode)}</span>

        <span className="text-base-content/20">|</span>

        {/* 当前时间 */}
        <span className="shrink-0 whitespace-nowrap text-base-content/50 font-mono text-[11px]">
          {now.toLocaleTimeString('zh-CN', { hour12: false })}
        </span>

        {/* 持仓 */}
        {position && (
          <>
            <span className="text-base-content/20">|</span>
            <div className="flex items-center gap-1.5 shrink-0 whitespace-nowrap">
              <span className={`font-semibold ${position.side === 'long' ? 'text-success' : 'text-error'}`}>
                {position.side === 'long' ? '多' : '空'} {position.size} 张
              </span>
              <span className={position.unrealized_pnl >= 0 ? 'text-success' : 'text-error'}>
                {position.unrealized_pnl >= 0 ? '+' : ''}{position.unrealized_pnl.toFixed(2)}
              </span>
            </div>
          </>
        )}
      </div>

      {/* 右侧：实时报价 */}
      {market && (
        <div className="flex items-center gap-3 shrink-0 whitespace-nowrap ml-4">
          <span className="text-base-content/40">{market.timeframe}</span>
          <span className="font-mono font-semibold text-sm">
            ${typeof market.price === 'number' ? market.price.toFixed(6) : market.price}
          </span>
          <span className={`font-mono ${(market.change ?? 0) >= 0 ? 'text-success' : 'text-error'}`}>
            {(market.change ?? 0) >= 0 ? '+' : ''}{((market.change ?? 0) * 100).toFixed(2)}%
          </span>
        </div>
      )}
    </div>
  )
}
