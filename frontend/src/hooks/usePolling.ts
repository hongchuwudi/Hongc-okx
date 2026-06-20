/**
 * 创建时间: 2025-06-21
 * 作者: hongchuwudi
 * 描述: 通用轮询 Hook — setInterval 封装，自动清理
 *
 * 包含:
 * - usePolling — 每隔 intervalMs 执行一次 callback，组件卸载时自动停止
 */

import { useEffect, useRef } from 'react'

/**
 * 通用轮询 Hook
 *
 * @param callback  要定时执行的函数
 * @param intervalMs  间隔（毫秒），传 0 或负数则跳过
 *
 * 使用示例:
 *   usePolling(refreshData, 5_000)
 */
export function usePolling(callback: () => void, intervalMs: number) {
  const cbRef = useRef(callback)
  cbRef.current = callback

  useEffect(() => {
    if (intervalMs <= 0) return

    const id = setInterval(() => cbRef.current(), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])
}
