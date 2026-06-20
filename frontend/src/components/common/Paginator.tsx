/**
 * 创建时间: 2026-06-17
 * 作者: hongchuwudi
 * 描述: 通用分页组件 — daisyUI btn + join 实现，lucide 图标
 *
 * 使用示例:
 *   // 完整模式（默认）
 *   <Paginator current={1} total={200} pageSize={20} onChange={(p, s) => {...}} />
 *
 *   // 完整模式 + 每页条数切换
 *   <Paginator current={1} total={200} pageSize={20} showSizeChanger
 *     pageSizeOptions={[10, 20, 50]} onChange={(p, s) => {...}} />
 *
 *   // 简单模式（仅上一页/下一页）
 *   <Paginator simple current={1} total={200} pageSize={20} onChange={(p) => {...}} />
 *
 * 包含:
 * - 组件: Paginator — 受控分页组件
 * - 类型: PaginatorProps / PageItem
 * - 函数: _buildPages — 构建页码数组（含省略号逻辑）
 */

import { useCallback, useState, type ReactNode } from 'react'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import FormInput from '@/components/common/FormInput'

// ===========================================================================
// 类型
// ===========================================================================

export interface PaginatorProps {
  current?: number
  total?: number
  pageSize?: number
  pageSizeOptions?: number[]
  showSizeChanger?: boolean
  showQuickJumper?: boolean
  showTotal?: (total: number, range: [number, number]) => ReactNode
  simple?: boolean
  size?: 'default' | 'small'
  disabled?: boolean
  onChange?: (page: number, pageSize: number) => void
}

type PageItem =
  | { type: 'page'; num: number }
  | { type: 'ellipsis'; key: 'e1' | 'e2'; direction: 'prev' | 'next' }

// ===========================================================================
// 页码构建
// ===========================================================================

function _buildPages(current: number, totalPages: number): PageItem[] {
  if (totalPages <= 1) return []
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => ({ type: 'page' as const, num: i + 1 }))
  }
  const pages: PageItem[] = [{ type: 'page', num: 1 }]
  if (current <= 4) {
    for (let i = 2; i <= Math.min(5, totalPages - 1); i++) pages.push({ type: 'page', num: i })
    if (totalPages > 6) pages.push({ type: 'ellipsis', key: 'e2', direction: 'next' })
  } else if (current >= totalPages - 3) {
    pages.push({ type: 'ellipsis', key: 'e1', direction: 'prev' })
    for (let i = Math.max(totalPages - 4, 2); i <= totalPages - 1; i++) pages.push({ type: 'page', num: i })
  } else {
    pages.push({ type: 'ellipsis', key: 'e1', direction: 'prev' })
    for (let i = current - 1; i <= current + 1; i++) pages.push({ type: 'page', num: i })
    pages.push({ type: 'ellipsis', key: 'e2', direction: 'next' })
  }
  pages.push({ type: 'page', num: totalPages })
  return pages
}

// ===========================================================================
// 组件
// ===========================================================================

export default function Paginator({
  current = 1, total = 0, pageSize = 10,
  pageSizeOptions = [10, 20, 50, 100],
  showSizeChanger = true, showQuickJumper = false,
  showTotal, simple = false, size = 'default', disabled = false,
  onChange,
}: PaginatorProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const safeCurrent = Math.max(1, Math.min(current, totalPages))
  const [hoverEllipsis, setHoverEllipsis] = useState<'e1' | 'e2' | null>(null)

  // 尺寸派生
  const isSmall = size === 'small'
  const btnSize = isSmall ? 'btn-sm' : 'btn-md'
  const formSize = isSmall ? 'xs' : 'sm'
  const iconPx = isSmall ? 14 : 18
  const gap = isSmall ? 'gap-1' : 'gap-1.5'
  const textSize = isSmall ? 'text-xs' : 'text-sm'

  const rangeStart = total === 0 ? 0 : (safeCurrent - 1) * pageSize + 1
  const rangeEnd = Math.min(safeCurrent * pageSize, total)

  const fire = useCallback((p: number, s: number) => {
    if (!disabled && onChange) onChange(p, s)
  }, [disabled, onChange])

  const handlePage = (p: number) => {
    const t = Math.max(1, Math.min(p, totalPages))
    if (t !== safeCurrent) fire(t, pageSize)
  }

  // jumper 值，用 state 管理避免受控冲突
  const [jumperValue, setJumperValue] = useState('')
  const handleJumperGo = () => {
    const v = parseInt(jumperValue, 10)
    if (!isNaN(v)) handlePage(v)
    setJumperValue('')
  }

  if (total === 0 && !showTotal) return null

  const pageItems = _buildPages(safeCurrent, totalPages)
  const canPrev = !disabled && safeCurrent > 1
  const canNext = !disabled && safeCurrent < totalPages

  // 通用幽灵按钮 class
  const ghostBtn = `btn btn-ghost ${btnSize} join-item`

  // ===================================================================
  // 简单模式
  // ===================================================================
  if (simple) {
    return (
      <div className={`flex items-center ${gap} ${textSize} text-base-content/80 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
        <button onClick={() => handlePage(safeCurrent - 1)} disabled={!canPrev} className={`btn btn-ghost ${btnSize}`} aria-label="上一页">
          <ChevronLeft size={iconPx} />
        </button>
        <span className="flex items-center gap-1.5 px-1.5 select-none">
          <span className="text-primary font-bold">{safeCurrent}</span>
          <span className="text-base-content/30">/</span>
          <span className="font-normal">{totalPages} 页</span>
          <span className="text-base-content/40 ml-0.5">({total} 条)</span>
        </span>
        <button onClick={() => handlePage(safeCurrent + 1)} disabled={!canNext} className={`btn btn-ghost ${btnSize}`} aria-label="下一页">
          <ChevronRight size={iconPx} />
        </button>
      </div>
    )
  }

  // ===================================================================
  // 完整模式
  // ===================================================================
  return (
    <div className={`flex flex-wrap items-center ${gap} ${textSize} text-base-content/70 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      {/* 总数 */}
      <span className="whitespace-nowrap font-normal mr-2 select-none">
        {showTotal ? showTotal(total, [rangeStart, rangeEnd]) : (
          <>
            当前 <span className="font-semibold text-base-content">{rangeStart}-{rangeEnd}</span>
            <span className="text-base-content/50"> / 共 </span>
            <span className="font-semibold text-base-content">{total}</span>
            <span className="text-base-content/50"> 条</span>
          </>
        )}
      </span>

      {/* 每页条数选择器 — join 按钮组，与页码按钮风格一致 */}
      {showSizeChanger && (
        <div className="join mr-1">
          {pageSizeOptions.map(opt => (
            <button
              key={opt}
              onClick={() => fire(1, opt)}
              disabled={disabled}
              className={`btn ${btnSize} join-item ${opt === pageSize ? 'btn-primary' : 'btn-ghost'}`}
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      {/* 页码按钮组 — daisyUI join */}
      <div className="join">
        {/* 上一页 */}
        <button onClick={() => handlePage(safeCurrent - 1)} disabled={!canPrev} className={ghostBtn} aria-label="上一页">
          <ChevronLeft size={iconPx} />
        </button>

        {pageItems.map(item => {
          if (item.type === 'ellipsis') {
            const isHovered = hoverEllipsis === item.key
            const isPrev = item.direction === 'prev'
            return (
              <button
                key={item.key}
                onMouseEnter={() => setHoverEllipsis(item.key)}
                onMouseLeave={() => setHoverEllipsis(null)}
                onClick={() => handlePage(safeCurrent + (isPrev ? -5 : 5))}
                className={`btn btn-ghost ${btnSize} join-item font-normal`}
                title={isPrev ? '向前 5 页' : '向后 5 页'}
              >
                {isHovered
                  ? (isPrev ? <ChevronsLeft size={iconPx} /> : <ChevronsRight size={iconPx} />)
                  : <span className="tracking-wider">...</span>
                }
              </button>
            )
          }
          const isActive = item.num === safeCurrent
          return (
            <button
              key={item.num}
              onClick={() => handlePage(item.num)}
              disabled={disabled}
              className={`btn ${btnSize} join-item ${isActive ? 'btn-primary' : 'btn-ghost'}`}
              aria-current={isActive ? 'page' : undefined}
            >
              {item.num}
            </button>
          )
        })}

        {/* 下一页 */}
        <button onClick={() => handlePage(safeCurrent + 1)} disabled={!canNext} className={ghostBtn} aria-label="下一页">
          <ChevronRight size={iconPx} />
        </button>
      </div>

      {/* 快速跳转 */}
      {showQuickJumper && (
        <span className="flex items-center gap-1.5 whitespace-nowrap ml-1 font-normal">
          <span className="text-base-content/50">前往</span>
          <FormInput
            size={formSize}
            type="number"
            value={jumperValue}
            onChange={setJumperValue}
            onKeyDown={e => { if (e.key === 'Enter') handleJumperGo() }}
            onBlur={handleJumperGo}
            placeholder=""
            disabled={disabled}
            className="w-12 text-center"
          />
          <span className="text-base-content/50">/ 共 {totalPages} 页</span>
        </span>
      )}
    </div>
  )
}
