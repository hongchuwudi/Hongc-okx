/**
 * 创建时间: 2026-06-15
 * 作者: hongchuwudi
 * 描述: 主题系统类型定义
 *
 * 包含:
 * - 接口: ThemeConfig — 单个主题配置
 * - 类型: ThemeMode — 主题标识
 */

import type { theme as antdTheme } from 'antd'

/** 主题标识 */
export type ThemeMode = 'light' | 'dark'

/** 单个主题配置 */
export interface ThemeConfig {
  /** 主题标识 */
  id: ThemeMode
  /** 中文名称 */
  label: string
  /** DaisyUI data-theme 值 */
  daisy: string
  /** Ant Design 主题算法 */
  antdAlgorithm: typeof antdTheme.defaultAlgorithm | typeof antdTheme.darkAlgorithm
  /** 图标（lucide-react 名称） */
  icon: string
}
