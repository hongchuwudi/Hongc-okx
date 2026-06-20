/**
 * 创建时间: 2025-06-21
 * 作者: hongchuwudi
 * 描述: 通用分页 Hook — 封装 page/pageSize/loading，配合 Paginator 使用
 *
 * 包含:
 * - usePagination — 管理分页状态，返回 Paginator 所需的所有 props
 */

import { useState, useCallback } from 'react'

interface PaginationState {
  page: number
  pageSize: number
  total: number
  loading: boolean
}

interface PaginationActions {
  /** 翻页/改 pageSize 时调用 */
  setPage: (page: number, pageSize: number) => void
  /** 供 load 函数更新 total 和关闭 loading */
  setTotal: (total: number) => void
  /** 开始加载 */
  startLoading: () => void
  /** 结束加载 */
  stopLoading: () => void
}

/**
 * 通用分页 Hook
 *
 * 使用示例:
 *   const { state, actions } = usePagination(20)
 *   const load = async (page: number, pageSize: number) => {
 *     actions.startLoading()
 *     const res = await fetchData(page, pageSize)
 *     actions.setTotal(res.total)
 *     actions.stopLoading()
 *   }
 *   return (
 *     <Paginator
 *       current={state.page}
 *       total={state.total}
 *       pageSize={state.pageSize}
 *       onChange={(p, ps) => { actions.setPage(p, ps); load(p, ps) }}
 *     />
 *   )
 */
export function usePagination(defaultPageSize = 20): {
  state: PaginationState
  actions: PaginationActions
} {
  const [state, setState] = useState<PaginationState>({
    page: 1,
    pageSize: defaultPageSize,
    total: 0,
    loading: true,
  })

  const setPage = useCallback((page: number, pageSize: number) => {
    setState(prev => ({ ...prev, page, pageSize }))
  }, [])

  const setTotal = useCallback((total: number) => {
    setState(prev => ({ ...prev, total }))
  }, [])

  const startLoading = useCallback(() => {
    setState(prev => ({ ...prev, loading: true }))
  }, [])

  const stopLoading = useCallback(() => {
    setState(prev => ({ ...prev, loading: false }))
  }, [])

  return {
    state,
    actions: { setPage, setTotal, startLoading, stopLoading },
  }
}
