/**
 * 创建时间: 2026-06-16
 * 作者: hongchuwudi
 * 描述: 交易相关常量 — K线周期、交易对选项
 */

/** K线图可用时间周期 */
export const TIMEFRAMES = [
  { label: '1m', value: '1m' },
  { label: '3m', value: '3m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1d', value: '1d' },
]

/** 回测用时间周期（不含 1m） */
export const BACKTEST_TIMEFRAMES = TIMEFRAMES.filter(t => t.value !== '1m')

/** 运行时配置用时间周期（不含 1d） */
export const RUNTIME_TIMEFRAMES = TIMEFRAMES.filter(t => t.value !== '1d')

/** 可用交易对 */
export const SYMBOLS = [
  { label: 'DOGE/USDT', value: 'DOGE/USDT:USDT' },
  { label: 'SHIB/USDT', value: 'SHIB/USDT:USDT' },
  { label: 'PEPE/USDT', value: 'PEPE/USDT:USDT' },
]
