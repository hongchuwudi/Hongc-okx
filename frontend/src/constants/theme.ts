/**
 * 创建时间: 2026-06-15
 * 作者: hongchuwudi
 * 描述: 主题常量 — light / dark 双主题
 *
 * 包含:
 * - THEMES — 可用主题列表
 * - DEFAULT_THEME — 默认主题（dark）
 * - STORAGE_KEY — localStorage 键名
 */

import { theme as antdTheme } from 'antd'
import type { ThemeConfig } from '@/types/theme'

export const THEMES: ThemeConfig[] = [
  {
    id: 'light',
    label: '浅色',
    daisy: 'light',
    antdAlgorithm: antdTheme.defaultAlgorithm,
  },
  {
    id: 'dark',
    label: '深色',
    daisy: 'dark',
    antdAlgorithm: antdTheme.darkAlgorithm,
  },
  {
    id: 'forest',
    label: '森林',
    daisy: 'forest',
    antdAlgorithm: antdTheme.darkAlgorithm,
  },
  {
    id: 'valentine',
    label: '情人节',
    daisy: 'valentine',
    antdAlgorithm: antdTheme.defaultAlgorithm,
  },
]

export const DEFAULT_THEME: ThemeConfig = THEMES[1] // dark

export const STORAGE_KEY = 'trading-ui-theme'

export function getThemeById(id: string): ThemeConfig {
  return THEMES.find(t => t.id === id) ?? DEFAULT_THEME
}
