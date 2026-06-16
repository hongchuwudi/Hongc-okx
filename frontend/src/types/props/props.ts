/**
 * Created: 2026-06-14
 * Author: hongchuwudi
 * Description: 组件 Props 类型
 */

import type { BacktestRunItem, BacktestTrade } from '../backtest'
import type { OhlcvBar } from '../kline'

// ChartCard — 权益曲线卡片
export interface ChartCardProps {
  title: string
  option: Record<string, unknown>
  key?: string | number
  notMerge?: boolean
}

// KlineChart — K线蜡烛图
export interface KlineChartProps {
  data: OhlcvBar[]
  trades?: BacktestTrade[]
}

// TradeTable — 交易明细表格
export interface TradeTableProps {
  trades: BacktestTrade[]
}

// FormFieldProps — 表单字段基础
export interface FormFieldProps {
  label: string
  field: string
}

// FormInputProps — 通用输入框（re-export from component）
export type { FormInputProps } from '@/components/common/FormInput'

// SelectField — 下拉选择字段
export interface SelectFieldProps extends FormFieldProps {
  value: string
  options: { label: string; value: string }[]
  onChange: (field: string, value: string) => void
}

// RunsTable — 历史回测记录表格
export interface RunsTableProps {
  runs: BacktestRunItem[]
  onView: (id: number) => void
  page: number
  pageSize: number
  totalPages: number
  total: number
  onPageChange: (page: number, pageSize: number) => void
}

// ResultCards — 绩效指标卡片
export interface ResultCardsProps {
  metrics: Record<string, number>
  symbol: string
}

// PositionCard — 持仓详情卡片
export interface PositionCardProps {
  /** 当前持仓，无持仓时为 null（此时卡片不渲染） */
  position: import('../dashboard').Position
  /** 当前最新价 */
  currentPrice: number
  /** 账户杠杆倍数 */
  leverage: number
  /** 建议止损价 */
  stopLoss: number | undefined
  /** 建议止盈价 */
  takeProfit: number | undefined
}

// StatusBar — 仪表盘顶栏
export interface StatusBarProps {
  agentMode: string
  market: import('../dashboard').MarketInfo | null
  position: import('../dashboard').Position | null
  aiSignal: import('../dashboard').AiSignal | null
  wsConnected: boolean
}

// MarkPointItem — ECharts 标记点
export interface MarkPointItem {
  coord: [number, number]
  name: string
  symbol: string
  symbolSize: number
  symbolRotate?: number
  itemStyle: { color: string; borderColor: string; borderWidth: number }
  label: {
    show: boolean
    formatter: string
    position: string
    distance: number
    fontSize: number
    fontWeight: string
    color: string
    backgroundColor: string
    borderRadius: number
    padding: [number, number]
  }
}
