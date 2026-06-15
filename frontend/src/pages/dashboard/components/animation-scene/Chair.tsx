/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 办公椅 — 五爪底座 + 坐垫 + 靠背 + 扶手
 *
 * 包含:
 * - 组件: Chair — 可配置位置、旋转角度、装饰色
 */
import React from 'react'

interface ChairProps {
  position: [number, number, number]
  rotationY?: number     // 整体绕 Y 轴旋转角度（弧度），默认 0
  color?: string
}

export default function Chair({ position, rotationY = 0, color = '#f59e0b' }: ChairProps) {
  return (
    <group position={position} rotation={[0, rotationY, 0]}>
      {/* ===== 五爪底座 ===== */}
      <mesh position={[0, 0.2, 0]}>
        <cylinderGeometry args={[0.08, 0.1, 0.4, 8]} />
        <meshStandardMaterial color="#D0CCC0" roughness={0.5} metalness={0.4} />
      </mesh>

      <mesh position={[0, 0.03, 0]}>
        <cylinderGeometry args={[0.25, 0.25, 0.06, 16]} />
        <meshStandardMaterial color="#C8C4B8" roughness={0.6} metalness={0.3} />
      </mesh>

      {Array.from({ length: 5 }).map((_, i) => {
        const angle = (i * 72 * Math.PI) / 180
        const legLength = 0.25
        const legX = Math.sin(angle) * legLength
        const legZ = Math.cos(angle) * legLength
        return (
          <group key={i}>
            <mesh
              position={[legX / 2, 0.03, legZ / 2]}
              rotation={[0, -angle, 0]}
            >
              <boxGeometry args={[legLength, 0.03, 0.04]} />
              <meshStandardMaterial color="#B0ACA0" roughness={0.6} metalness={0.5} />
            </mesh>
            <mesh position={[legX, 0.02, legZ]}>
              <sphereGeometry args={[0.03, 6, 6]} />
              <meshStandardMaterial color="#333333" roughness={0.3} />
            </mesh>
          </group>
        )
      })}

      {/* ===== 坐垫 ===== */}
      <mesh position={[0, 0.45, 0]}>
        <boxGeometry args={[0.5, 0.06, 0.5]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.7} />
      </mesh>

      {/* ===== 靠背 ===== */}
      <group position={[0, 0.45 + 0.06, -0.25]}>
        {/* 支架 */}
        <mesh position={[-0.18, 0.12, 0]}>
          <boxGeometry args={[0.04, 0.32, 0.04]} />
          <meshStandardMaterial color="#D0CCC0" roughness={0.5} metalness={0.4} />
        </mesh>
        <mesh position={[0.18, 0.12, 0]}>
          <boxGeometry args={[0.04, 0.32, 0.04]} />
          <meshStandardMaterial color="#D0CCC0" roughness={0.5} metalness={0.4} />
        </mesh>

        {/* 靠背面 */}
        <mesh position={[0, 0.32, 0]}>
          <boxGeometry args={[0.42, 0.24, 0.03]} />
          <meshStandardMaterial color="#F5F0E8" roughness={0.7} />
        </mesh>

        {/* 装饰 */}
        <mesh position={[0, 0.32, 0.017]}>
          <boxGeometry args={[0.2, 0.08, 0.008]} />
          <meshStandardMaterial color={color} roughness={0.5} />
        </mesh>
      </group>

      {/* ===== 扶手 ===== */}
      {[-1, 1].map((side) => (
        <group key={`arm-${side}`}>
          <mesh position={[side * 0.24, 0.45 - 0.03, 0.12]}>
            <boxGeometry args={[0.04, 0.18, 0.04]} />
            <meshStandardMaterial color="#D0CCC0" roughness={0.5} metalness={0.4} />
          </mesh>
          <mesh position={[side * 0.24, 0.45 + 0.06, 0.12]}>
            <boxGeometry args={[0.06, 0.03, 0.24]} />
            <meshStandardMaterial color="#F5F0E8" roughness={0.7} />
          </mesh>
        </group>
      ))}
    </group>
  )
}