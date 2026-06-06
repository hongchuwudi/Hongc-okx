/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: main.tsx React应用入口
 * 描述: 应用入口文件，渲染 React 根组件至 DOM
 *
 * 包含:
 * - 组件: App — 根组件渲染入口
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

// 渲染 React 根组件到 DOM 节点
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
