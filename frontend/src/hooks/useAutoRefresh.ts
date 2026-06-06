/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: useAutoRefresh.ts 自动刷新Hook
 * 描述: 自动刷新 Hook，基于 setInterval 实现定时轮询回调函数
 *
 * 包含:
 * - Hook: useAutoRefresh — 定时执行回调的通用 Hook，支持启用/禁用和自定义间隔
 */
import { useEffect, useRef } from 'react'

// 通用自动刷新 Hook — 按指定间隔执行回调，支持动态启用/禁用
export function useAutoRefresh(
  callback: () => void,
  enabled: boolean,
  intervalMs = 10000,
) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) return
    const id = setInterval(() => savedCallback.current(), intervalMs)
    return () => clearInterval(id)
  }, [enabled, intervalMs])
}
