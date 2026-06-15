/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测表单下拉选项常量
 */

export const STRATEGIES = [
  { label: '技术指标', value: 'technical' },
  { label: 'DeepSeek AI', value: 'deepseek' },
]

export const SYMBOLS = [
  { label: 'DOGE/USDT:USDT', value: 'DOGE/USDT:USDT' },
  { label: 'BTC/USDT:USDT', value: 'BTC/USDT:USDT' },
  { label: 'ETH/USDT:USDT', value: 'ETH/USDT:USDT' },
]

export const TIMEFRAMES = [
  { label: '3 分钟', value: '3m' },
  { label: '5 分钟', value: '5m' },
  { label: '15 分钟', value: '15m' },
  { label: '30 分钟', value: '30m' },
  { label: '1 小时', value: '1h' },
  { label: '4 小时', value: '4h' },
  { label: '1 天', value: '1d' },
]

export const CAPITALS = [
  { label: '1 USDT', value: '1' },
  { label: '10 USDT', value: '10' },
  { label: '15 USDT', value: '15' },
  { label: '50 USDT', value: '50' },
  { label: '100 USDT', value: '100' },
  { label: '200 USDT', value: '200' },
  { label: '500 USDT', value: '500' },
  { label: '1000 USDT', value: '1000' },
  { label: '5000 USDT', value: '5000' },
]

export const POSITION_RATIOS = [
  { label: '10%', value: '0.1' },
  { label: '20%', value: '0.2' },
  { label: '30%', value: '0.3' },
  { label: '50%', value: '0.5' },
  { label: '80%', value: '0.8' },
  { label: '100%', value: '1.0' },
]

export const FEE_RATES = [
  { label: '0.05% (Maker)', value: '0.0005' },
  { label: '0.1% (Taker)', value: '0.001' },
]

export const WARMUPS = [
  { label: '20 条', value: '20' },
  { label: '50 条', value: '50' },
  { label: '100 条', value: '100' },
  { label: '200 条', value: '200' },
]

export const DATA_LIMITS = [
  { label: '100 条', value: '100' },
  { label: '150 条', value: '150' },
  { label: '200 条', value: '200' },
  { label: '250 条', value: '250' },
  { label: '300 条', value: '300' },
  { label: '400 条', value: '400' },
  { label: '500 条', value: '500' },
  { label: '1000 条', value: '1000' },
  { label: '1500 条', value: '1500' },
  { label: '2000 条', value: '2000' },
]

// DeepSeek AI 激进程度
export const TEMPERATURES = [
  { label: '极度保守 (0.05)', value: '0.05' },
  { label: '保守 (0.1)', value: '0.1' },
  { label: '中等 (0.3)', value: '0.3' },
  { label: '激进 (0.6)', value: '0.6' },
  { label: '疯狂 (1.0)', value: '1.0' },
]