/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: L 形桌面 — 主翼 2×1 + 侧翼 1×2 + 挡板
 */

import { TILE } from './constants'

interface Props { cx: number; cz: number }

export default function LDesk({ cx, cz }: Props) {
  const h = 0.75
  const thick = 0.02

  return (
    <group>
      {/* 主翼 — 沿后墙，2×1 */}
      <mesh position={[cx, h, cz - TILE / 2]}>
        <boxGeometry args={[TILE * 2, thick, TILE]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.7} />
      </mesh>
      {/* 侧翼 — 沿侧墙，1×2，Y 微调 0.003 防穿模 */}
      <mesh position={[cx - TILE / 2, h + 0.003, cz]}>
        <boxGeometry args={[TILE, thick, TILE * 2]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.7} />
      </mesh>
      {/* 主翼后缘挡板 — 贴后墙外侧 */}
      <mesh position={[cx, h - 0.35, cz - TILE]}>
        <boxGeometry args={[TILE * 2, 0.7, 0.02]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
      </mesh>
      {/* 侧翼左缘挡板 — 贴侧墙外侧 */}
      <mesh position={[cx - TILE, h - 0.35, cz]}>
        <boxGeometry args={[0.02, 0.7, TILE * 2]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
      </mesh>
      {/* 主翼右侧挡板 — 对齐主翼 Z 范围 */}
      <mesh position={[cx + TILE, h - 0.35, cz - TILE / 2]}>
        <boxGeometry args={[0.02, 0.7, TILE]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
      </mesh>
    </group>
  )
}
