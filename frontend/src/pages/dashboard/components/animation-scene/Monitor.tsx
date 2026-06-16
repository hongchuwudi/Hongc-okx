/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 显示器 — 底座 + 支撑柱 + 屏幕外壳 + 发光屏 + 细边框 + 摄像头
 */

interface Props { cx: number; cz: number; color: string }

export default function Monitor({ cx, cz, color }: Props) {
  const sw = 0.8
  const sh = 0.5
  const st = 0.03

  const innerW = sw - 0.08
  const innerH = sh - 0.06
  const screenCenterY = 0.06 + 0.1 + sh / 2
  const screenFrontZ = st / 2 + 0.005
  const borderZ = screenFrontZ + 0.002
  const borderThickness = 0.02
  const borderDepth = 0.01

  return (
    <group position={[cx - 0.55, 0.76, cz - 0.55]} rotation={[0, Math.PI / 4, 0]}>
      {/* ===== 底座 ===== */}
      <mesh position={[0, 0.03, 0]}>
        <boxGeometry args={[0.35, 0.06, 0.16]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
      </mesh>

      {/* ===== 支撑柱 ===== */}
      <mesh position={[0, 0.06 + 0.05, 0]}>
        <cylinderGeometry args={[0.03, 0.03, 0.1, 8]} />
        <meshStandardMaterial color="#D0CCC0" roughness={0.5} metalness={0.3} />
      </mesh>

      {/* ===== 屏幕外壳 ===== */}
      <mesh position={[0, screenCenterY, 0]}>
        <boxGeometry args={[sw, sh, st]} />
        <meshStandardMaterial color="#F5F0E8" roughness={0.5} />
      </mesh>

      {/* ===== 发光屏幕（底色） ===== */}
      <mesh position={[0, screenCenterY, screenFrontZ]}>
        <planeGeometry args={[innerW, innerH]} />
        <meshBasicMaterial color={color} />
      </mesh>

      {/* ===== 屏幕内边框（深色细框） ===== */}
      <group position={[0, screenCenterY, borderZ]}>
        <mesh position={[0, innerH / 2 + borderThickness / 2, 0]}>
          <boxGeometry args={[innerW, borderThickness, borderDepth]} />
          <meshStandardMaterial color="#333333" roughness={0.4} />
        </mesh>
        <mesh position={[0, -innerH / 2 - borderThickness / 2, 0]}>
          <boxGeometry args={[innerW, borderThickness, borderDepth]} />
          <meshStandardMaterial color="#333333" roughness={0.4} />
        </mesh>
        <mesh position={[-innerW / 2 - borderThickness / 2, 0, 0]}>
          <boxGeometry args={[borderThickness, innerH, borderDepth]} />
          <meshStandardMaterial color="#333333" roughness={0.4} />
        </mesh>
        <mesh position={[innerW / 2 + borderThickness / 2, 0, 0]}>
          <boxGeometry args={[borderThickness, innerH, borderDepth]} />
          <meshStandardMaterial color="#333333" roughness={0.4} />
        </mesh>
      </group>

      {/* ===== 摄像头 ===== */}
      <mesh position={[0, screenCenterY + sh / 2 + 0.015, st / 2 + 0.005]}>
        <cylinderGeometry args={[0.012, 0.012, 0.02, 8]} />
        <meshStandardMaterial color="#333333" roughness={0.3} />
      </mesh>

      {/* ===== 屏幕光 ===== */}
      <pointLight position={[0, screenCenterY, 0.2]} color={color} intensity={0.3} distance={3} />
    </group>
  )
}
