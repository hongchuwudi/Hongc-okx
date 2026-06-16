/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 格子间主组件 — 组装墙/桌/柜/显示器/键盘/椅子
 */

import { Text } from '@react-three/drei'
import type { CubicleProps } from '@/types/scene'
import GlassWall from './GlassWall'
import LDesk from './LDesk'
import Cabinet from './Cabinet'
import Monitor from './Monitor'
import Keyboard from './Keyboard'
import Chair from './Chair'
import DeskToys from './DeskToys'
import { GRID, TILE } from './constants'

function w(gx: number, gy: number): [number, number] {
  return [(gx - GRID / 2 + 0.5) * TILE, (gy - GRID / 2 + 0.5) * TILE]
}

export default function Cubicle({ gx, gy, color, flip, chairRotationY }: CubicleProps) {
  const [cx, cz] = w(gx + 0.5, gy + 0.5)
  const half = TILE

  return (
    <group position={[cx, 0, cz]}>
      <group scale={[flip ? -1 : 1, 1, 1]}>
        {/* 后墙 */}
        <GlassWall cx={0} cz={-half} wd={half * 2} dp={0.02} color={color} />
        {/* 左侧墙 */}
        <GlassWall cx={-half} cz={0} wd={0.02} dp={half * 2} color={color} />

        {/* hongchu 标志 — 翻转后纠正文字 */}
        <Text position={[0, 0.92, -half + 0.015]} fontSize={0.28} color={color}
          scale={flip ? [-1, 1, 1] : [1, 1, 1]}>
          hongchu
        </Text>

        {/* L 形桌面 */}
        <LDesk cx={0} cz={0} />

        {/* 侧边储物柜 */}
        <Cabinet cx={-half + TILE / 2} cz={0.75 * half} />

        {/* 显示器 */}
        <Monitor cx={0} cz={0} color={color} />

        {/* 桌面玩偶 — 放主翼桌面右侧，避开键盘 */}
        <DeskToys position={[0.4, 0, -0.5]} color={color} />

        {/* 键盘 */}
        <Keyboard cx={-0.26} cz={-0.26} />

        {/* 椅子 */}
        <Chair
          position={[0.7, 0, 0.7]}
          rotationY={chairRotationY ?? (flip ? Math.PI / 4 : -Math.PI / 4)}
          color={color}
        />
      </group>
    </group>
  )
}
