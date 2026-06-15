/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 键盘 — 主体 + 键帽阵列 + 指示灯
 */

interface Props { cx: number; cz: number }

export default function Keyboard({ cx, cz }: Props) {
  const kw = 0.025; const kd = 0.022; const kh = 0.005
  const cols = 14; const rows = 5
  const tw = cols * kw + (cols - 1) * 0.005
  const td = rows * kd + (rows - 1) * 0.003
  const sx = -tw / 2 + kw / 2
  const sz = -td / 2 + kd / 2

  return (
    <group position={[cx, 0.75, cz - 0.05]} rotation={[0.03, Math.PI / 4, 0]}>
      {/* 键盘主体 */}
      <mesh position={[0, 0.015, 0]}>
        <boxGeometry args={[0.5, 0.03, 0.16]} />
        <meshStandardMaterial color="#D4D0C8" roughness={0.7} />
      </mesh>
      {/* 键帽阵列 */}
      {Array.from({ length: rows }).map((_, r) =>
        Array.from({ length: cols }).map((_, c) => (
          <mesh key={`${r}-${c}`} position={[sx + c * (kw + 0.005), 0.033, sz + r * (kd + 0.003)]}>
            <boxGeometry args={[kw, kh, kd]} />
            <meshStandardMaterial color="#4A4A4A" roughness={0.9} />
          </mesh>
        ))
      )}
      {/* 指示灯 */}
      <mesh position={[sx + (cols - 1.5) * (kw + 0.005), 0.035, sz + 0.5 * (kd + 0.003)]}>
        <sphereGeometry args={[0.008, 8, 8]} />
        <meshBasicMaterial color="#7CFC00" />
      </mesh>
    </group>
  )
}
