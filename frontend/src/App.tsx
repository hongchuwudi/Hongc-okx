/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 应用入口 — React Router + zustand stores
 *
 * 状态管理全部迁移至 zustand（stores/），无 Context Provider
 */

import { useEffect } from 'react'
import { BrowserRouter, useRoutes } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import { useDashboardStore } from './stores/dashboardStore'
import { useThemeStore } from './stores/themeStore'
import routes from './routes'

function AppInit() {
  const init = useDashboardStore(s => s.init)
  const destroy = useDashboardStore(s => s.destroy)
  const theme = useThemeStore(s => s.theme)

  useEffect(() => {
    init()
    return () => destroy()
  }, [init, destroy])

  return (
    <ConfigProvider theme={{ algorithm: theme.antdAlgorithm, token: { colorPrimary: '#3370FF', borderRadius: 10 } }}>
      {useRoutes(routes)}
    </ConfigProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInit />
    </BrowserRouter>
  )
}
