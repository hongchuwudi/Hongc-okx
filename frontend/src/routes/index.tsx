/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 路由配置 — React Router 路由表
 */

import { type RouteObject } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import Dashboard from '../pages/dashboard'
import Backtest from '../pages/backtest'
import Logs from '../pages/logs'
import Prompts from '../pages/prompts'
import Trades from '../pages/trades'
import Decisions from '../pages/decisions'

const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/backtest', element: <Backtest /> },
      { path: '/logs', element: <Logs /> },
      { path: '/trades', element: <Trades /> },
      { path: '/decisions', element: <Decisions /> },
      { path: '/prompts', element: <Prompts /> },
    ],
  },
]

export default routes
