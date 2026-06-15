/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: 回测参数说明
 */

interface ParamItem { title: string; desc: string }

export const PARAMS: ParamItem[] = [
  { title: '策略', desc: '技术指标：基于 MA/RSI/MACD/布林带等传统指标生成信号。DeepSeek AI：调用大模型分析行情，每 N 根 K 线请求一次。' },
  { title: '交易对', desc: '回测的交易品种，格式为 基础币/计价币:USDT，如 DOGE/USDT:USDT。' },
  { title: 'K线周期', desc: '每根 K 线的时间跨度。周期越短交易越频繁，周期越长信号越稳定。' },
  { title: '初始资金', desc: '回测开始时的本金（USDT）。后续开仓按仓位比例计算实际投入金额。' },
  { title: '仓位比例', desc: '每次开仓使用当前权益的百分比。如 50% 表示每次用一半资金开仓，剩下的留作缓冲。' },
  { title: '手续费率', desc: '每笔交易（开仓+平仓）的手续费率。Taker 0.1% 是市价单费率，Maker 0.05% 是限价单费率。' },
  { title: '预热期', desc: '回测开始后跳过前面 N 根 K 线不交易，只用于计算技术指标（如 MA50 需要至少 50 根）。' },
  { title: '数据量', desc: '从交易所拉取的 K 线总条数。OKX 单次最多约 300 条，系统会自动分页拉取更多。实际可用 K 线 = 数据量 - 预热期。' },
]
