/**
 * 创建时间: 2025-06-21
 * 作者: hongchuwudi
 * 描述: 自动滚动到底部 Hook — 新内容到达时自动滚，用户手动滚走后停止
 *
 * 包含:
 * - useAutoScroll — 返回 ref（挂到滚动容器上）+ 回到底部按钮状态 + 滚动方法
 */

import { useRef, useState, useCallback, useEffect } from 'react'

interface AutoScrollResult {
  /** 挂到滚动容器的 ref */
  containerRef: React.RefObject<HTMLDivElement | null>
  /** 是否显示"回到底部"按钮 */
  showScrollBtn: boolean
  /** 手动滚到底部 */
  scrollToBottom: () => void
  /** 监听 onScroll 事件的回调 */
  onScroll: () => void
}

/**
 * 自动滚动 Hook — 用于实时日志流等场景
 *
 * 使用示例:
 *   const { containerRef, showScrollBtn, scrollToBottom } = useAutoScroll(deps)
 *   return (
 *     <div ref={containerRef}>
 *       {items.map(...)}
 *       {showScrollBtn && <button onClick={scrollToBottom}>回到底部</button>}
 *     </div>
 *   )
 *
 * @param deps  当 deps 变化时触发自动滚动（通常传 [list.length]）
 */
export function useAutoScroll(deps: unknown[]): AutoScrollResult {
  const containerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [showScrollBtn, setShowScrollBtn] = useState(false)

  const scrollToBottom = useCallback(() => {
    const el = containerRef.current
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      setAutoScroll(true)
      setShowScrollBtn(false)
    }
  }, [])

  // 用户手动滚动时检测是否在底部
  const handleScroll = useCallback(() => {
    const el = containerRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40
    setAutoScroll(atBottom)
    if (atBottom) setShowScrollBtn(false)
  }, [])

  // 新内容到达时自动滚
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
    if (!autoScroll) {
      setShowScrollBtn(true)
    }
  // deps 由调用方传入
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { containerRef, showScrollBtn, scrollToBottom, onScroll: handleScroll }
}
