/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 侧边储物柜 — 四条腿 + 柜体 + 双门板 + 把手
 */

interface Props { cx: number; cz: number }

export default function Cabinet({ cx, cz }: Props) {
  const bw = 1; const bh = 0.73; const bd = 0.5
  const gap = 0.02
  const doorWz = (bd - gap) / 2
  const doorH = bh - 0.06
  const doorThick = 0.01
  const doorX = bw / 2 + doorThick / 2
  const legH = 0.05; const legR = 0.04; const legIn = 0.12
  const hr = 0.015; const hh = 0.07; const hz = 0.08

  return (
    <group position={[cx, 0, cz]}>
      {/* 四条柜腿 */}
      {[[bw / 2 - legIn, bd / 2 - legIn], [-bw / 2 + legIn, bd / 2 - legIn],
        [bw / 2 - legIn, -bd / 2 + legIn], [-bw / 2 + legIn, -bd / 2 + legIn]
      ].map(([lx, lz], i) => (
        <mesh key={`leg-${i}`} position={[lx, legH / 2, lz]}>
          <cylinderGeometry args={[legR, legR + 0.005, legH, 8]} />
          <meshStandardMaterial color="#E8E3D8" roughness={0.6} />
        </mesh>
      ))}
      {/* 柜体 */}
      <mesh position={[0, bh / 2, 0]}>
        <boxGeometry args={[bw, bh, bd]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
      </mesh>
      {/* 顶盖 + 底座 */}
      <mesh position={[0, bh + 0.01, 0]}>
        <boxGeometry args={[bw + 0.04, 0.02, bd + 0.04]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.6} />
      </mesh>
      <mesh position={[0, 0.01, 0]}>
        <boxGeometry args={[bw + 0.03, 0.02, bd + 0.03]} />
        <meshStandardMaterial color="#EDE8DD" roughness={0.6} />
      </mesh>
      {/* 双门板（+X 面） */}
      {[doorWz / 2 + gap / 2, -doorWz / 2 - gap / 2].map((dz, i) => (
        <group key={`door-${i}`}>
          <mesh position={[doorX, bh / 2, dz]}>
            <boxGeometry args={[doorThick, doorH, doorWz]} />
            <meshStandardMaterial color="#F5F0E8" roughness={0.6} />
          </mesh>
          <mesh position={[doorX + doorThick / 2 + 0.002, bh / 2, dz]}>
            <boxGeometry args={[0.004, 0.012, doorWz * 0.6]} />
            <meshStandardMaterial color="#E0DCD0" roughness={0.7} />
          </mesh>
          {/* 把手 */}
          <mesh position={[doorX + doorThick / 2 + hr, bh / 2, dz + (i === 0 ? hz : -hz)]}>
            <cylinderGeometry args={[hr, hr, hh, 8]} />
            <meshStandardMaterial color="#C8C4B8" roughness={0.4} metalness={0.3} />
          </mesh>
        </group>
      ))}
      {/* 门缝 */}
      <mesh position={[doorX + doorThick / 2 + 0.001, bh / 2, 0]}>
        <boxGeometry args={[0.002, doorH, gap]} />
        <meshStandardMaterial color="#888" roughness={0.5} />
      </mesh>
    </group>
  )
}
