/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 路由配置 — React Router 路由表
 */

import { type RouteObject } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout'
import Dashboard from '../pages/dashboard'
import Backtest from '../pages/backtest'
import Agents from '../pages/agents'
import Trades from '../pages/trades'
import Decisions from '../pages/decisions'
import Playground from '../pages/playground'

const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/backtest', element: <Backtest /> },
      { path: '/agents', element: <Agents /> },
      { path: '/trades', element: <Trades /> },
      { path: '/decisions', element: <Decisions /> },
      { path: '/playground', element: <Playground /> },
    ],
  },
]

export default routes
