/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: AgentOffice.tsx AI智能体办公场景
 * 描述: AI 智能体办公场景，展示分析师/风控官/复盘师/交易员四角色协作状态动画
 *
 * 包含:
 * - 类型: A — 智能体状态描述对象
 * - 类型: AgentReports — 各 Agent 报告文本映射
 * - 函数: mk — 创建默认智能体状态
 * - 函数: parseReason — 解析 AI 决策原因 JSON
 * - 常量: IDS — 智能体 ID 列表
 * - 常量: NAMES — 智能体中文名列表
 * - 常量: ACCENTS — 各角色主题色列表
 * - 常量: ROLES — 各角色英文名列表
 * - 常量: JOB — 各角色职责描述映射
 * - 组件: AgentOffice — 四宫格 Agent 状态展示组件
 */
import { useState, useEffect, useRef } from 'react'
import TradingFloor from '../trading/TradingFloor'

// 智能体状态对象类型 — 包含 ID、状态、显示文本和倒计时
interface A { id: string; state: string; text: string; textTimer: number }
// 四名 Agent 的 ID、中文名、主题色和英文角色名
const IDS = ['market', 'risk', 'memory', 'trader']
const NAMES = ['分析师', '风控官', '复盘师', '交易员']
const ACCENTS = ['#ffd66e', '#ff6e6e', '#6ee7ff', '#a7ff83']
const ROLES = ['Market', 'Risk', 'Memory', 'Trader']

// 创建默认智能体状态（空闲、无文本）
function mk(): A { return { id: '', state: 'idle', text: '', textTimer: 0 } }

// Agent 报告文本映射类型
interface AgentReports { market?: string; risk?: string; memory?: string }
// 解析 AI 决策原因 JSON 字符串
function parseReason(r: string): { reason: string; agents?: AgentReports } | null {
  try { return JSON.parse(r) } catch { return null }
}

// Agent 办公室场景 — 展示四 Agent 状态动画，根据 AI reason 驱动状态流转
export default function AgentOffice({ aiReason, lastUpdate }: { aiReason: string; lastUpdate: number | null }) {
  const [agents, setAgents] = useState<A[]>(Array.from({ length: 4 }, mk))
  const triggered = useRef('')
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    if (!aiReason || aiReason === triggered.current) return
    const p = parseReason(aiReason); if (!p?.agents) return
    triggered.current = aiReason
    const map: Record<string, string> = {
      market: p.agents.market || '', risk: p.agents.risk || '',
      memory: p.agents.memory || '', trader: p.reason || '',
    }
    timers.current.forEach(clearTimeout); timers.current = []
    setAgents(prev => prev.map((a, i) => ({ ...a, state: 'walking', text: '', textTimer: 0 })))
    timers.current.push(setTimeout(() => {
      setAgents(prev => prev.map((a, i) => ({ ...a, state: 'working', text: map[IDS[i]] || '', textTimer: 200 })))
      timers.current.push(setTimeout(() => {
        setAgents(prev => prev.map(a => ({ ...a, state: 'done', textTimer: a.textTimer })))
      }, 3000))
    }, 1200))
    return () => timers.current.forEach(clearTimeout)
  }, [aiReason])

  useEffect(() => {
    const t = setInterval(() => {
      if (lastUpdate && Date.now() - lastUpdate > 120000)
        setAgents(prev => prev.map(a => ({ ...a, state: 'idle', text: '', textTimer: 0 })))
    }, 15000)
    return () => clearInterval(t)
  }, [lastUpdate])

  // 倒计时回 idle
  useEffect(() => {
    const t = setInterval(() => {
      setAgents(prev => prev.map(a => {
        if (a.textTimer > 0) return { ...a, textTimer: a.textTimer - 1 }
        if (a.textTimer === 0 && a.state === 'done') return { ...a, state: 'idle' }
        return a
      }))
    }, 100)
    return () => clearInterval(t)
  }, [])

  // 状态标签和颜色映射
  const stateLabel: Record<string, string> = { idle: '空闲', walking: '移动中', working: '工作中', done: '已完成' }
  const stateColor: Record<string, string> = { idle: 'var(--color-base-content)', walking: '#ffd66e', working: '#a7ff83', done: '#6ee7ff' }
// 各 Agent 职责描述映射
const JOB: Record<string, string> = {
    market: '分析K线形态与趋势方向',
    risk: '评估风险敞口与仓位建议',
    memory: '复盘历史决策与胜率模式',
    trader: '综合团队意见下达最终指令',
  }

  return (
    <div className="agent-layout" style={{ gap: 6, height: '100%', minHeight: 360 }}>
      <TradingFloor aiReason={aiReason} lastUpdate={lastUpdate} />

      <style>{`
        .agent-layout { display: flex; flex-direction: column; }
        @media (min-width: 768px) { .agent-layout { display: grid; grid-template-columns: 3fr 2fr; } }
      `}</style>

      {/* 四宫格 — 铺满容器 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: 6, height: '100%' }}>
        {agents.map((a, i) => (
          <div key={IDS[i]} style={{
            background: 'var(--color-base-100)',
            border: '1px solid var(--color-base-300)',
            borderRadius: 10, padding: 12, display: 'flex', flexDirection: 'column', gap: 8,
          }}>
            {/* 顶行: 头像圆点 + 名字 + 状态 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {/* 彩色小圆点代替 border-top */}
              <div style={{
                width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                background: ACCENTS[i],
                boxShadow: a.state !== 'idle' ? `0 0 6px ${ACCENTS[i]}` : 'none',
                opacity: a.state === 'idle' ? .3 : 1,
                transition: 'opacity .3s, box-shadow .3s',
              }} />
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-base-content)', lineHeight: 1.3 }}>
                  {NAMES[i]}
                </div>
                <div style={{ fontSize: 10, color: 'var(--color-base-content)', opacity: .35, lineHeight: 1.2, marginTop: 1 }}>
                  {JOB[IDS[i]]}
                </div>
              </div>
              <span style={{
                flexShrink: 0, fontSize: 9, fontWeight: 500, padding: '2px 8px', borderRadius: 4,
                background: 'var(--color-base-200)',
                color: 'var(--color-base-content)',
                opacity: a.state === 'idle' ? .35 : .7,
              }}>
                {stateLabel[a.state]}
              </span>
            </div>

            {/* 输出内容 */}
            {a.text && a.state !== 'idle' ? (
              <div style={{
                fontSize: 11, color: 'var(--color-base-content)', opacity: .55,
                lineHeight: 1.5, flex: 1,
                overflow: 'hidden', textOverflow: 'ellipsis',
              }}>
                {a.text.slice(0, 80)}
              </div>
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--color-base-content)', opacity: .12 }}>
                  — 等待信号 —
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
