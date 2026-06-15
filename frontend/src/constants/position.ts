/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 持仓相关常量 — 强平估算、方向映射、显示配置
 *
 * 包含:
 * - 函数: estLiquidationPrice — 估算强平价格（OKX 永续合约公式）
 * - 常量: SIDE_LABEL — 持仓方向中文映射
 * - 常量: SIDE_COLOR — 持仓方向颜色映射
 */

/** 维持保证金率（OKX 永续合约约 0.5%） */
const MMR = 0.005

/**
 * 估算强平价格（参考 OKX 永续合约公式）
 * 多头: entry * (1 - 1/leverage + mmr)
 * 空头: entry * (1 + 1/leverage - mmr)
 */
export function estLiquidationPrice(
  entry: number, leverage: number, side: 'long' | 'short',
): number {
  if (side === 'long') return entry * (1 - 1 / leverage + MMR)
  return entry * (1 + 1 / leverage - MMR)
}

/** 持仓方向中文标签 */
export const SIDE_LABEL: Record<string, string> = {
  long: '做多',
  short: '做空',
}

/** 持仓方向颜色（long=绿涨, short=红跌） */
export const SIDE_COLOR: Record<string, { text: string; bg: string }> = {
  long: { text: 'text-success', bg: 'badge-success' },
  short: { text: 'text-error', bg: 'badge-error' },
}
