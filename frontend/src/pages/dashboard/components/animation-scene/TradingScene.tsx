/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 3D 等距交易大厅主场景 + 右上角相机控制按钮 — 7 个 Agent 工位
 *
 * Contains:
 * - AGENT_DESKS — 7 个 Agent 工位布局（坐标 + 颜色 + 朝向）
 * - Component: TradingScene — 3D Canvas 场景
 * - Component: CameraControls — 右上角控制按钮
 */

import { useState, useCallback, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import Floor from './Floor'
import Cubicle from './Cubicle'
import SceneCamera from './SceneCamera'
import CameraControls from './CameraControls'
import { AGENT_INFO } from '@/constants/agent'

/** 7 个 Agent 工位坐标和朝向（颜色从 AGENT_INFO 统一取） */
const DESK_LAYOUT = [
  { name: 'scheduler',      gx: 13, gy: 24, chairRot: 0 },
  { name: 'analyst',        gx: 19, gy: 24, chairRot: 0 },
  { name: 'reviewer',       gx: 25, gy: 24, chairRot: 0 },
  { name: 'super_analyst',  gx: 31, gy: 24, chairRot: 0 },
  { name: 'risk',           gx: 16, gy: 13, chairRot: Math.PI },
  { name: 'trader',         gx: 22, gy: 13, chairRot: Math.PI },
  { name: 'solo',           gx: 28, gy: 13, chairRot: Math.PI },
]

export default function TradingScene() {
  const [rotateEnabled, setRotateEnabled] = useState(false)
  const [resetKey, setResetKey] = useState(0)

  const toggleRotate = useCallback(() => setRotateEnabled(v => !v), [])
  const resetView = useCallback(() => setResetKey(k => k + 1), [])

  return (
    <div className="w-full rounded-xl overflow-hidden border border-base-300 relative h-[60vh] min-h-[400px] max-h-[800px]">
      <Canvas
        camera={{ position: [3, 11, 10], fov: 50 }}
        gl={{ antialias: true }}
      >
        {/* 光照 */}
        <ambientLight intensity={0.7} />
        <directionalLight position={[8, 10, 3]} intensity={1.2} />
        <directionalLight position={[-5, 3, -5]} intensity={0.4} />

        {/* 棋盘格地板 */}
        <Floor />

        {/* 7 个 Agent 工位 */}
        {DESK_LAYOUT.map((desk) => (
          <Cubicle
            key={desk.name}
            gx={desk.gx}
            gy={desk.gy}
            color={AGENT_INFO[desk.name]?.color ?? '#9ca3af'}
            flip={desk.chairRot !== 0}
            chairRotationY={desk.chairRot || undefined}
          />
        ))}

        {/* 摄像机 */}
        <SceneCamera rotateEnabled={rotateEnabled} resetKey={resetKey} />
      </Canvas>

      {/* 右上角相机控制按钮组 */}
      <CameraControls
        rotateEnabled={rotateEnabled}
        onToggleRotate={toggleRotate}
        onResetView={resetView}
      />
    </div>
  )
}
