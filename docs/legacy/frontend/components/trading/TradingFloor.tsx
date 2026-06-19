/**
 * 创建时间: 2026-06-06
 * 作者: hongchuwudi
 * 文件名: TradingFloor.tsx 交易大厅Phaser场景
 * 描述: 基于 Phaser.js 的 3D 等距交易大厅场景，四名 Agent 在办公室中自由行走并响应用户查询
 *
 * 包含:
 * - 常量: TW/TH/GW/GH — 等距瓦片和网格尺寸
 * - 常量: AGENTS — 四名 Agent 工位配置信息
 * - 类: TradingScene — Phaser 游戏场景，管理地板、房间、工位及 Agent BFS 寻路行走动画
 * - 类型: AR — Agent 报告文本映射
 * - 函数: pR — 解析 AI 原因 JSON
 * - 组件: TradingFloor — React 包裹层，管理 Phaser 画布生命周期和状态同步
 */
import { useRef, useEffect, useState, useCallback } from 'react'
import * as Phaser from 'phaser'

// ---- 照搬 GameAgent ISO 常量 ----
const TW = 64; const TH = 32
const GW = 22; const GH = 16

// 获取当前主题配色方案（亮色/暗色）
function getTheme() {
  const dark = typeof document !== 'undefined' && document.documentElement.dataset.theme !== 'light'
  return dark
    ? { floor: 0x111a35, floorStroke: 0x1a2446, carpet: 0x2b355f, carpetStroke: 0x6ee7ff, bg: 0x0b1020, wallFill: 0x0f1730, wallStroke: 0x2b355f }
    : { floor: 0xe1e4ea, floorStroke: 0xc5c9d0, carpet: 0xd5dae0, carpetStroke: 0x3370ff, bg: 0xf0f2f5, wallFill: 0xd5dae0, wallStroke: 0xbcc3cc }
}
// 等距投影坐标转换 — 将网格坐标转为屏幕像素坐标
function iso(gx: number, gy: number) { return { x: (gx - gy) * TW / 2, y: (gx + gy) * TH / 2 } }

// 五名 Agent 工位配置 — 含 ID、名称、部门、主题色和网格坐标
const AGENTS = [
  { id: 'scheduler', name: '调度师', dept: '决策协调部', accent: 0xf59e0b, gx: 8, gy: 2 },
  { id: 'analyst', name: '分析师', dept: '行情研究部', accent: 0xffd66e, gx: 4, gy: 6 },
  { id: 'reviewer', name: '复盘师', dept: '战略研究部', accent: 0x6ee7ff, gx: 12, gy: 6 },
  { id: 'risk', name: '风控官', dept: '风险管理部', accent: 0xff6e6e, gx: 4, gy: 12 },
  { id: 'trader', name: '交易员', dept: '交易执行部', accent: 0xa7ff83, gx: 12, gy: 12 },
]

// Phaser 游戏场景 — 管理地板/房间/墙壁渲染，Agent BFS 寻路行走动画
class TradingScene extends Phaser.Scene {
  private agents: Map<string, { av: Phaser.GameObjects.Image; si: Phaser.GameObjects.Image; st: Phaser.GameObjects.Text; lb: Phaser.GameObjects.Text; state: string; bx: number; by: number; bob: Phaser.Tweens.Tween | null }> = new Map()

  constructor() { super('trading') }

  // 加载并生成等距纹理：地板、地毯、墙壁、门、桌子、Agent 等
  preload() {
    const T = getTheme()
    this._tex('floor', TW, TH, g => {
      g.fillStyle(T.floor, 1); g.lineStyle(1, T.floorStroke, 0.45)
      g.beginPath(); g.moveTo(TW / 2, 0); g.lineTo(TW, TH / 2); g.lineTo(TW / 2, TH); g.lineTo(0, TH / 2); g.closePath()
      g.fillPath(); g.strokePath()
    })
    this._tex('carpet', TW, TH, g => {
      g.fillStyle(T.carpet, 1); g.lineStyle(1, T.carpetStroke, 0.25)
      g.beginPath(); g.moveTo(TW / 2, 0); g.lineTo(TW, TH / 2); g.lineTo(TW / 2, TH); g.lineTo(0, TH / 2); g.closePath()
      g.fillPath(); g.strokePath()
    })
    this._tex('wall', TW, TH + 26, g => {
      const by = 18; const h = 26
      g.fillStyle(T.wallFill, 1); g.lineStyle(1, T.wallStroke, 0.9)
      g.beginPath(); g.moveTo(TW / 2, by); g.lineTo(TW, by + TH / 2); g.lineTo(TW / 2, by + TH); g.lineTo(0, by + TH / 2); g.closePath()
      g.fillPath(); g.strokePath()
      g.fillStyle(T.bg, 0.55); g.fillRect(TW / 2 - 2, by + TH, 4, h)
      g.fillStyle(T.bg === 0x0b1020 ? 0xe7ecff : 0x333333, 0.08); g.fillRect(6, by + 6, 6, TH + 10)
    })
    this._tex('door', TW, TH + 26, g => {
      const by = 18; const h = 26
      g.fillStyle(T.floor, 1)
      g.beginPath(); g.moveTo(TW / 2, by); g.lineTo(TW, by + TH / 2); g.lineTo(TW / 2, by + TH); g.lineTo(0, by + TH / 2); g.closePath()
      g.fillPath(); g.lineStyle(1, T.wallStroke, 0.9); g.strokePath()
      g.fillStyle(0x6b4f2a, 1); g.fillRect(TW / 2 - 8, by + TH - 2, 16, h)
      g.fillStyle(0xe7ecff, 0.6); g.fillRect(TW / 2 + 4, by + TH + 10, 2, 2)
    })
    this._tex('desk', 96, 64, g => {
      g.fillStyle(0x3e2b16, 1); g.fillRect(8, 48, 8, 16); g.fillRect(80, 48, 8, 16)
      g.fillStyle(0x6b4f2a, 1); g.fillRect(0, 38, 96, 16)
      g.fillStyle(0x000000, 0.15); g.fillRect(0, 38, 96, 2)
      g.fillStyle(0x2b355f, 1); g.fillRect(34, 14, 28, 24)
      g.fillStyle(0x6ee7ff, 0.25); g.fillRect(36, 16, 24, 20)
    })
    this._tex('agent', 32, 32, g => {
      g.fillStyle(0x000000, 0.2); g.fillEllipse(16, 28, 20, 6)
      g.fillStyle(0x5fd6ff, 1); g.fillRect(8, 16, 16, 10)
      g.fillStyle(0xffd1b3, 1); g.fillRect(10, 6, 12, 12)
      g.fillStyle(0x2b1d12, 1); g.fillRect(10, 6, 12, 3)
      g.fillStyle(0x111111, 1); g.fillRect(13, 10, 2, 2); g.fillRect(18, 10, 2, 2)
    })
    this._tex('sidle', 20, 20, g => { g.fillStyle(0x0b1020, 0.85); g.fillCircle(10, 10, 7); g.lineStyle(1, 0xc9d3ff, 0.6); g.strokeCircle(10, 10, 5); g.fillStyle(0xc9d3ff, 0.8); g.fillCircle(10, 10, 3) })
    this._tex('swork', 20, 20, g => { g.fillStyle(0x0b1020, 0.85); g.fillCircle(10, 10, 7); g.lineStyle(1, 0xa7ff83, 0.8); g.strokeCircle(10, 10, 5); g.fillStyle(0xa7ff83, 1); g.fillCircle(10, 10, 4) })
    this._tex('sdone', 20, 20, g => { g.fillStyle(0x0b1020, 0.85); g.fillCircle(10, 10, 7); g.lineStyle(1, 0x6ee7ff, 0.7); g.strokeCircle(10, 10, 5); g.fillStyle(0x6ee7ff, 1); g.fillCircle(10, 10, 4) })
  }

  // 纹理生成工具方法 — 用 Graphics 绘制后生成可复用的纹理
  private _tex(k: string, w: number, h: number, d: (g: Phaser.GameObjects.Graphics) => void) { const g = this.add.graphics(); d(g); g.generateTexture(k, w, h); g.destroy() }

  // 创建场景 — 铺设地板、房间、工位，初始化 Agent 并启动自动漫游
  create() {
    const T = getTheme()
    this.cameras.main.setBounds(-600, -500, 3200, 2600)
    this.cameras.main.centerOn(130, 210)
    this.cameras.main.setZoom(1.2)
    ;(window as any).__tradingZoom = 120
    this.cameras.main.setBackgroundColor(T.bg)

    // 地板 — 照搬 GameAgent px_iso_floor
    for (let gx = 0; gx < GW; gx++)
      for (let gy = 0; gy < GH; gy++) {
        const p = iso(gx, gy)
        this.add.image(p.x, p.y, 'floor').setOrigin(0.5, 0).setDepth(p.y - 2000)
      }

    // 房间
    this._room(0, 1, 3.5, 13, 3, 8, '会议室', 0x6ee7ff)        // 左侧大会议室
    this._room(16, 1.5, 5, 5, 17, 5, '茶水间', 0xffd66e)     // 右上
    this._room(16, 7.5, 5, 4.5, 17, 10, '卫生间', 0xc9d3ff)  // 右下

    // 会议桌 + 4 椅子
    const mt = iso(1.7, 7.5)
    const tableGfx = this.add.graphics().setDepth(mt.y + 100)
    tableGfx.fillStyle(0x6b4f2a, 1); tableGfx.fillRect(mt.x - 40, mt.y - 10, 80, 20)
    tableGfx.lineStyle(2, 0x3e2b16, 1); tableGfx.strokeRect(mt.x - 40, mt.y - 10, 80, 20)
    ;[[-35, -16], [35, -16], [-35, 16], [35, 16]].forEach(([dx, dy]) => {
      tableGfx.fillStyle(0x2b355f, 1); tableGfx.fillRect(mt.x + dx, mt.y + dy, 12, 10)
    })

    // Agent 工位
    for (const a of AGENTS) {
      const p = iso(a.gx, a.gy)
      this.add.image(p.x, p.y + 18, 'desk').setOrigin(0.5, 0.5).setDepth(p.y + 10)
      const av = this.add.image(p.x - 24, p.y - 8, 'agent').setOrigin(0.5, 0.5).setDepth(p.y + 100)
      const si = this.add.image(p.x - 18, p.y - 24, 'sidle').setOrigin(0.5, 0.5).setDepth(p.y + 101)
      const lb = this.add.text(p.x - 38, p.y + 42, `${a.name} · ${a.dept}`, { fontFamily: 'monospace', fontSize: '11px', color: '#e7ecff', resolution: 2 }).setOrigin(0.5, 0).setDepth(p.y + 102)
      const st = this.add.text(p.x - 38, p.y - 42, '', { fontFamily: 'monospace', fontSize: '10px', color: '#c9d3ff', backgroundColor: 'rgba(11,16,32,0.78)', padding: { left: 4, right: 4, top: 2, bottom: 2 }, resolution: 2 }).setOrigin(0.5, 0.5).setDepth(p.y + 103).setAlpha(0)
      const bob = this.tweens.add({ targets: av, y: av.y - 3, duration: 800 + Math.random() * 500, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' })
      this.agents.set(a.id, { av, si, st, lb, state: 'idle', bx: av.x, by: av.y, bob })
    }

    // 拖拽 + 缩放
    let dx = 0; let dy = 0
    this.input.on('pointerdown', (p: Phaser.Input.Pointer) => { dx = p.x; dy = p.y })
    this.input.on('pointermove', (p: Phaser.Input.Pointer) => { if (p.isDown) { this.cameras.main.scrollX -= (p.x - dx) / this.cameras.main.zoom; this.cameras.main.scrollY -= (p.y - dy) / this.cameras.main.zoom; dx = p.x; dy = p.y } })
    this.input.on('wheel', (_p: unknown, _o: unknown, _dx: number, dy: number) => {
      const z = Math.max(0.3, Math.min(2, this.cameras.main.zoom - dy * 0.001))
      this.cameras.main.setZoom(z)
      ;(window as any).__tradingZoom = Math.round(z * 100)
    })

    // 有目的走动 — 全地图可去
    const spots: [number, number, number][] = [
      [1.7, 3, 1], [1.7, 6, 1], [1.7, 10, 1], [1.7, 12, 1],  // 会议室 (weight 1)
      [17.5, 3, 2], [17.5, 5, 2],                              // 茶水间 (weight 2)
      [17.5, 9, 2], [17.5, 10, 2],                              // 卫生间 (weight 2)
    ]
    // 同事工位也加入
    AGENTS.forEach(a => spots.push([a.gx, a.gy, 3]))  // 工位 weight 3

    // 加权随机选点算法 — 房间权重高于工位，增加 Agent 漫游多样性
    function pickSpot() {
      const total = spots.reduce((s, sp) => s + sp[2], 0)
      let r = Math.random() * total
      for (const sp of spots) { r -= sp[2]; if (r <= 0) return sp }
      return spots[0]
    }

    // === 照搬 GameAgent: BFS 寻路 + 逐格步进 ===
    const deskBlocks = new Set<string>()
    const blocked = new Set<string>()
    const k = (gx: number, gy: number) => `${Math.round(gx)},${Math.round(gy)}`
    AGENTS.forEach(a => deskBlocks.add(k(a.gx, a.gy)))  // 办公桌
    // 把办公桌加入 blocked（供 BFS 使用）
    deskBlocks.forEach(b => blocked.add(b))
    // 房间墙壁 — 只阻墙线本身，留门
    const doors = new Set([k(3,8), k(17,5), k(17,10)])
    // 会议室 (gx:0-3.5, gy:1-14): 墙在 gx=-1, gx=4, gy=0, gy=14
    for (let y = 0; y <= 14; y++) { if (!doors.has(k(-1, y))) blocked.add(k(-1, y)); if (!doors.has(k(4, y))) blocked.add(k(4, y)) }
    for (let x = -1; x <= 4; x++) { if (!doors.has(k(x, 0))) blocked.add(k(x, 0)); if (!doors.has(k(x, 14))) blocked.add(k(x, 14)) }
    // 茶水间 (gx:16-21, gy:1.5-6.5)
    for (let y = 1; y <= 7; y++) { if (!doors.has(k(15, y))) blocked.add(k(15, y)); if (!doors.has(k(22, y))) blocked.add(k(22, y)) }
    for (let x = 15; x <= 22; x++) { if (!doors.has(k(x, 1))) blocked.add(k(x, 1)); if (!doors.has(k(x, 7))) blocked.add(k(x, 7)) }
    // 卫生间 (gx:16-21, gy:7.5-12)
    for (let y = 7; y <= 12; y++) { if (!doors.has(k(15, y))) blocked.add(k(15, y)); if (!doors.has(k(22, y))) blocked.add(k(22, y)) }
    for (let x = 15; x <= 22; x++) { if (!doors.has(k(x, 7))) blocked.add(k(x, 7)); if (!doors.has(k(x, 12))) blocked.add(k(x, 12)) }
    // 地图边界
    for (let x = -1; x <= GW+1; x++) { blocked.add(k(x, -2)); blocked.add(k(x, -1)); blocked.add(k(x, GH+1)); blocked.add(k(x, GH+2)) }
    for (let y = -2; y <= GH+2; y++) { blocked.add(k(-2, y)); blocked.add(k(-1, y)); blocked.add(k(GW+1, y)); blocked.add(k(GW+2, y)) }

    // BFS 寻路算法 — 在 blocked 网格中寻找最短路径，允许穿过起点和目标点
    function bfs(fx: number, fy: number, tx: number, ty: number): { gx: number; gy: number }[] {
      const sk = k(Math.round(fx), Math.round(fy)); const gk = k(Math.round(tx), Math.round(ty))
      if (sk === gk) return []
      const q: string[] = [sk]; const from = new Map<string, string>(); const vis = new Set<string>([sk])
      // 允许穿过自己的桌子（起点）+ 目标点
      const allowed = new Set([sk, gk])
      while (q.length) {
        const c = q.shift()!; const [cx, cy] = c.split(',').map(Number)
        for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
          const nk = k(cx+dx, cy+dy)
          if (vis.has(nk)) continue
          if (blocked.has(nk) && !allowed.has(nk)) continue
          vis.add(nk); from.set(nk, c)
          if (nk === gk) { const p: {gx:number;gy:number}[] = []; let cur = nk; while (cur !== sk) { const [x,y]=cur.split(',').map(Number); p.push({gx:x,gy:y}); cur = from.get(cur)! }; p.reverse(); return p }
          q.push(nk)
        }
      }
      return []
    }

    const moving = new Map<string, boolean>()
    const pos = new Map<string, { gx: number; gy: number }>()
    AGENTS.forEach(a => { moving.set(a.id, false); pos.set(a.id, { gx: a.gx, gy: a.gy }) })

    const S = this
    // 逐格步进动画 — 按 BFS 路径一步步移动 Agent
    function walkStep(aid: string, path: { gx: number; gy: number }[], i: number) {
      const d = S.agents.get(aid)!
      if (i >= path.length) {
        moving.set(aid, false)
        const l = path[path.length-1]; pos.get(aid)!.gx = l.gx; pos.get(aid)!.gy = l.gy
        return
      }
      const p = iso(path[i].gx, path[i].gy)
      // 离开当前格时释放占用
      if (i > 0) {
        const prev = path[i-1]
        if (deskBlocks.has(k(prev.gx, prev.gy))) blocked.delete(k(prev.gx, prev.gy))
      }
      // 即将进入时占用
      blocked.add(k(path[i].gx, path[i].gy))
      S.tweens.add({
        targets: d.av, x: p.x-24, y: p.y-8, duration: 400, ease: 'Linear',
        onUpdate: () => { d.si.x = d.av.x+6; d.si.y = d.av.y-16; d.st.x = d.av.x; d.st.y = d.av.y-34 },
        onComplete: () => walkStep(aid, path, i+1)
      })
    }

    S.time.addEvent({ delay: 2500, loop: true, callback: () => {
      const free = AGENTS.filter(a => S.agents.get(a.id)?.state === 'idle' && !moving.get(a.id))
      if (free.length === 0) return
      const a = free[Math.floor(Math.random() * free.length)]
      const spot = pickSpot()
      const pg = pos.get(a.id)!
      const path = bfs(pg.gx, pg.gy, Math.round(spot[0]), Math.round(spot[1]))
      if (path.length === 0) return
      moving.set(a.id, true)
      walkStep(a.id, path, 0)
    }})
  }

  // 创建房间（地毯 + 墙壁 + 门 + 标签）
  private _room(gx: number, gy: number, gw: number, gh: number, dgx: number, dgy: number, label: string, color: number) {
    for (let x = gx; x < gx + gw; x++)
      for (let y = gy; y < gy + gh; y++) {
        const p = iso(x, y)
        this.add.image(p.x, p.y, 'carpet').setOrigin(0.5, 0).setDepth(p.y - 1500)
      }
    for (let x = gx; x < gx + gw; x++) { this._w(x, gy - 1, x === dgx && gy - 1 === dgy); this._w(x, gy + gh, x === dgx && gy + gh === dgy) }
    for (let y = gy; y < gy + gh; y++) { this._w(gx - 1, y, gx - 1 === dgx && y === dgy); this._w(gx + gw, y, gx + gw === dgx && y === dgy) }
    this._w(dgx, dgy, true)
    const lp = iso(gx + gw / 2, gy + gh / 2)
    this.add.text(lp.x, lp.y + 4, label, { fontFamily: 'monospace', fontSize: '11px', color: '#' + color.toString(16).padStart(6, '0'), resolution: 2 }).setOrigin(0.5).setDepth(lp.y + 600)
  }

  // 放置墙壁或门（door 参数决定纹理选择）
  private _w(gx: number, gy: number, door: boolean) {
    const p = iso(gx, gy)
    this.add.image(p.x, p.y - 18, door ? 'door' : 'wall').setOrigin(0.5, 0).setDepth(p.y + 60)
  }

  // 更新指定 Agent 的状态（idle/working/done）并切换纹理和显示文本
  updateStatus(id: string, state: string, text: string) {
    const a = this.agents.get(id); if (!a) return; a.state = state
    const accent = AGENTS.find(x => x.id === id)?.accent ?? 0xc9d3ff
    const color = '#' + accent.toString(16).padStart(6, '0')
    if (state === 'working') { a.si.setTexture('swork'); a.si.setTint(accent); if (text) { a.st.setText(text.slice(0, 50)); a.st.setAlpha(1); a.st.setStyle({ ...a.st.style, color }) } }
    else if (state === 'done') { a.si.setTexture('sdone'); a.si.setTint(accent); if (text) { a.st.setText(text.slice(0, 50)); a.st.setAlpha(1); a.st.setStyle({ ...a.st.style, color }) } }
    else { a.si.setTexture('sidle'); a.si.clearTint(); a.st.setAlpha(0) }
  }
}

// 解析 AI 原因 JSON（agent_reports 格式: {reason, agents: {scheduler, analyst, reviewer, risk, trader}}）
interface AR { scheduler?: string; analyst?: string; reviewer?: string; risk?: string; trader?: string }
function pR(r: string): { reason: string; agents?: AR } | null { try { return JSON.parse(r) } catch { return null } }

// TradingFloor React 组件 — 管理 Phaser 画布生命周期，同步 AI 推理状态到场景
export default function TradingFloor({ aiReason, lastUpdate }: { aiReason: string; lastUpdate: number | null }) {
  const cr = useRef<HTMLDivElement>(null)
  const gr = useRef<Phaser.Game | null>(null)
  const sr = useRef<TradingScene | null>(null)
  const tr = useRef('')
  const [zoom, setZoom] = useState(120)
  const [themeKey, setThemeKey] = useState(0)

  // 主题切换 → 强制重建场景
  useEffect(() => {
    const obs = new MutationObserver(() => setThemeKey(k => k + 1))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => obs.disconnect()
  }, [])

  useEffect(() => {
    if (!cr.current || gr.current) return
    const g = new Phaser.Game({
      type: Phaser.AUTO, width: 1200, height: 700,
      parent: cr.current,
      backgroundColor: document.documentElement.dataset.theme !== 'light' ? '#0b1020' : '#f0f2f5',
      render: { antialias: true, pixelArt: false, roundPixels: true },
      scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
      scene: TradingScene,
    })
    gr.current = g
    g.events.on('ready', () => { sr.current = g.scene.getScene('trading') as TradingScene })
    // 每 500ms 轮询缩放值
    const zi = setInterval(() => { const z = (window as any).__tradingZoom; if (z) setZoom(z) }, 500)
    return () => { g.destroy(true); gr.current = null; clearInterval(zi) }
  }, [themeKey])

  useEffect(() => {
    if (!aiReason || aiReason === tr.current) return
    const p = pR(aiReason); if (!p?.agents) return; tr.current = aiReason
    const map: Record<string, string> = { scheduler: p.agents.scheduler || '', analyst: p.agents.analyst || '', reviewer: p.agents.reviewer || '', risk: p.agents.risk || '', trader: p.agents.trader || '' }
    const s = sr.current; if (!s) return
    AGENTS.forEach(a => s.updateStatus(a.id, 'working', ''))
    setTimeout(() => { AGENTS.forEach(a => s.updateStatus(a.id, 'done', map[a.id] || '')); setTimeout(() => { AGENTS.forEach(a => s.updateStatus(a.id, 'idle', '')) }, 4000) }, 1500)
  }, [aiReason])

  useEffect(() => { const t = setInterval(() => { if (lastUpdate && Date.now() - lastUpdate > 120000) { const s = sr.current; if (s) AGENTS.forEach(a => s.updateStatus(a.id, 'idle', '')) } }, 15000); return () => clearInterval(t) }, [lastUpdate])

  return (
    <div ref={cr} style={{ width: '100%', height: '100%', borderRadius: 10, overflow: 'hidden', border: '1px solid var(--color-base-300)', position: 'relative' }}>
      {/* 缩放指示器 */}
      <div style={{
        position: 'absolute', top: 8, right: 10, zIndex: 10,
        background: 'rgba(11,16,32,0.75)', color: '#c9d3ff',
        fontSize: 10, fontFamily: 'monospace', fontWeight: 600,
        padding: '2px 8px', borderRadius: 999,
        border: '1px solid rgba(201,211,255,0.2)',
        pointerEvents: 'none',
      }}>
        {zoom}%
      </div>
    </div>
  )
}
