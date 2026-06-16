/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 通用分页组件 — 受控分页器，API 对标 Ant Design Pagination，daisyUI 样式
 *
 * 包含:
 * - 组件: Paginator — 受控分页组件
 * - 函数: _buildPages — 构建页码数组（含省略号逻辑）
 */

import React, { useCallback, useRef, type ReactNode } from 'react'

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

export interface PaginatorProps {
  /** 当前页码 */
  current?: number
  /** 数据总数 */
  total?: number
  /** 每页条数 */
  pageSize?: number
  /** 可选的每页条数 */
  pageSizeOptions?: number[]
  /** 是否显示每页条数选择器 */
  showSizeChanger?: boolean
  /** 是否显示快速跳转输入框 */
  showQuickJumper?: boolean
  /** 自定义总数显示 */
  showTotal?: (total: number, range: [number, number]) => ReactNode
  /** 简单模式：仅上一页 / 当前页/总页数 / 下一页 */
  simple?: boolean
  /** 组件尺寸 */
  size?: 'default' | 'small'
  /** 禁用整个分页 */
  disabled?: boolean
  /** 页码或每页条数变化回调 */
  onChange?: (page: number, pageSize: number) => void
}

// ---------------------------------------------------------------------------
// 页码构建
// ---------------------------------------------------------------------------

type PageItem = { type: 'page'; num: number } | { type: 'ellipsis'; key: string }

const ELLIPSIS: PageItem = { type: 'ellipsis', key: '...' }

function _buildPages(current: number, totalPages: number): PageItem[] {
  if (totalPages <= 1) return []

  // <=7 页：全部展示
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => ({ type: 'page' as const, num: i + 1 }))
  }

  const pages: PageItem[] = [{ type: 'page', num: 1 }]

  // 当前页靠近开头
  if (current <= 4) {
    for (let i = 2; i <= Math.min(5, totalPages - 1); i++) {
      pages.push({ type: 'page', num: i })
    }
    if (totalPages > 6) pages.push({ type: 'ellipsis', key: 'e2' })
  }
  // 当前页靠近结尾
  else if (current >= totalPages - 3) {
    pages.push({ type: 'ellipsis', key: 'e1' })
    for (let i = Math.max(totalPages - 4, 2); i <= totalPages - 1; i++) {
      pages.push({ type: 'page', num: i })
    }
  }
  // 当前页在中间
  else {
    pages.push({ type: 'ellipsis', key: 'e1' })
    for (let i = current - 1; i <= current + 1; i++) {
      pages.push({ type: 'page', num: i })
    }
    pages.push({ type: 'ellipsis', key: 'e2' })
  }

  pages.push({ type: 'page', num: totalPages })
  return pages
}

// ---------------------------------------------------------------------------
// 组件
// ---------------------------------------------------------------------------

export default function Paginator({
  current = 1,
  total = 0,
  pageSize = 10,
  pageSizeOptions = [10, 20, 50, 100],
  showSizeChanger = true,
  showQuickJumper = false,
  showTotal,
  simple = false,
  size = 'default',
  disabled = false,
  onChange,
}: PaginatorProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const safeCurrent = Math.max(1, Math.min(current, totalPages))
  const jumperRef = useRef<HTMLInputElement>(null)

  const sz = size === 'small' ? 'xs' : 'sm'
  const btnClass = `btn btn-${sz}`
  const inputClass = `input input-${sz} input-bordered`
  const selectClass = `select select-${sz} select-bordered`
  const disabledClass = 'btn-disabled pointer-events-none opacity-50'

  // 数据范围
  const rangeStart = total === 0 ? 0 : (safeCurrent - 1) * pageSize + 1
  const rangeEnd = Math.min(safeCurrent * pageSize, total)

  const fire = useCallback(
    (p: number, s: number) => {
      if (!disabled && onChange) onChange(p, s)
    },
    [disabled, onChange],
  )

  const handlePage = (p: number) => {
    if (p >= 1 && p <= totalPages && p !== safeCurrent) fire(p, pageSize)
  }

  const handleSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    fire(1, Number(e.target.value))
  }

  const handleJump = () => {
    const el = jumperRef.current
    if (!el) return
    const v = parseInt(el.value, 10)
    if (v >= 1 && v <= totalPages) {
      fire(v, pageSize)
      el.value = ''
    }
  }

  const handleJumpKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleJump()
  }

  // ── 不显示的条件 ──
  if (total === 0 && !showTotal) return null

  // ── 简单模式 ──
  if (simple) {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={() => handlePage(safeCurrent - 1)}
          disabled={disabled || safeCurrent <= 1}
          className={`${btnClass} btn-ghost ${disabled || safeCurrent <= 1 ? disabledClass : ''}`}
        >
          上一页
        </button>
        <span className={`px-2 text-${sz} text-base-content/70`}>
          {safeCurrent} / {totalPages}
        </span>
        <button
          onClick={() => handlePage(safeCurrent + 1)}
          disabled={disabled || safeCurrent >= totalPages}
          className={`${btnClass} btn-ghost ${disabled || safeCurrent >= totalPages ? disabledClass : ''}`}
        >
          下一页
        </button>
      </div>
    )
  }

  // ── 完整模式 ──
  const pages = _buildPages(safeCurrent, totalPages)

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* ── 总数显示 ── */}
      {showTotal ? (
        <span className={`text-${sz} text-base-content/70`}>
          {showTotal(total, [rangeStart, rangeEnd])}
        </span>
      ) : (
        <span className={`text-${sz} text-base-content/70`}>
          共 {total} 条
        </span>
      )}

      {/* ── 页码按钮组 ── */}
      <div className="join">
        <button
          onClick={() => handlePage(safeCurrent - 1)}
          disabled={disabled || safeCurrent <= 1}
          className={`${btnClass} join-item ${disabled || safeCurrent <= 1 ? disabledClass : ''}`}
        >
          上一页
        </button>

        {pages.map((item, idx) => {
          if (item.type === 'ellipsis') {
            return (
              <span
                key={item.key}
                className={`${btnClass} join-item btn-disabled !opacity-50`}
              >
                ...
              </span>
            )
          }
          const isActive = item.num === safeCurrent
          return (
            <button
              key={item.num}
              onClick={() => handlePage(item.num)}
              disabled={disabled}
              className={`${btnClass} join-item ${isActive ? 'btn-primary' : ''}`}
            >
              {item.num}
            </button>
          )
        })}

        <button
          onClick={() => handlePage(safeCurrent + 1)}
          disabled={disabled || safeCurrent >= totalPages}
          className={`${btnClass} join-item ${disabled || safeCurrent >= totalPages ? disabledClass : ''}`}
        >
          下一页
        </button>
      </div>

      {/* ── 每页条数选择器 ── */}
      {showSizeChanger && (
        <select
          value={pageSize}
          onChange={handleSizeChange}
          disabled={disabled}
          className={selectClass}
        >
          {pageSizeOptions.map(opt => (
            <option key={opt} value={opt}>
              {opt} 条/页
            </option>
          ))}
        </select>
      )}

      {/* ── 快速跳转 ── */}
      {showQuickJumper && (
        <span className="flex items-center gap-1">
          <span className={`text-${sz} text-base-content/60`}>跳至</span>
          <input
            ref={jumperRef}
            type="number"
            min={1}
            max={totalPages}
            disabled={disabled}
            onKeyDown={handleJumpKey}
            onBlur={handleJump}
            placeholder=""
            className={`${inputClass} w-14`}
          />
        </span>
      )}
    </div>
  )
}
