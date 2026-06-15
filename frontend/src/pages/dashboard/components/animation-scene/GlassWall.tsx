/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 毛玻璃隔断 — 半透明面板 + 四边金属细框
 */

interface Props {
  cx: number; cz: number
  wd: number; dp: number
  color: string
}

export default function GlassWall({ cx, cz, wd, dp, color }: Props) {
  const gh = 0.35; const gy = 0.75

  return (
    <group position={[cx, gy + gh / 2, cz]}>
      {/* 毛玻璃主体 */}
      <mesh>
        <boxGeometry args={[wd, gh, dp]} />
        <meshStandardMaterial color={color} roughness={0.1} transparent opacity={0.25} />
      </mesh>
      {/* 四边金属细框 */}
      {[
        [0, gh / 2, 0, wd, 0.015, dp + 0.005],
        [0, -gh / 2, 0, wd, 0.015, dp + 0.005],
        [wd / 2, 0, 0, 0.015, gh, dp + 0.005],
        [-wd / 2, 0, 0, 0.015, gh, dp + 0.005],
      ].map(([bx, by, bz, bw, bh, bd], i) => (
        <mesh key={i} position={[bx, by, bz]}>
          <boxGeometry args={[bw, bh, bd]} />
          <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
        </mesh>
      ))}
    </group>
  )
}
