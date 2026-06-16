/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: K线数据类型
 */

/**
 * OHLCV K线数据条
 * 表示一根 K 线（蜡烛）的完整行情数据
 */
export interface OhlcvBar {
  /** 时间戳（毫秒），K 线的起始时间 */
  t: number
  /** 开盘价 */
  o: number
  /** 最高价 */
  h: number
  /** 最低价 */
  l: number
  /** 收盘价 */
  c: number
  /** 成交量 */
  v: number
}

