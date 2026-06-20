/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 桌面装饰 — 盆栽 + 马克杯 + 笔筒 + 散落文件
 *
 * 包含:
 * - 组件: DeskToys — 可配置摆放位置和主题色
 */

interface DeskToysProps {
  position: [number, number, number]  // 整体摆放中心，Y 会统一抬高到桌面高度
  color: string                        // 主题色（用于马克杯和笔）
}

export default function DeskToys({ position, color }: DeskToysProps) {
  const [cx, _, cz] = position
  const deskY = 0.76  // 桌面顶面 Y

  return (
    <group position={[cx, deskY, cz]}>
      {/* ===== 1. 小盆栽 — 放在右边靠后 ===== */}
      <group position={[0.4, 0, -0.4]}>
        {/* 花盆 */}
        <mesh position={[0, 0.04, 0]}>
          <cylinderGeometry args={[0.06, 0.05, 0.08, 8]} />
          <meshStandardMaterial color="#E8E3D8" roughness={0.7} />
        </mesh>
        {/* 泥土 */}
        <mesh position={[0, 0.08, 0]}>
          <cylinderGeometry args={[0.05, 0.055, 0.02, 8]} />
          <meshStandardMaterial color="#8B7355" roughness={0.9} />
        </mesh>
        {/* 叶子（三个小绿色球体） */}
        <mesh position={[0.02, 0.1, 0.02]}>
          <sphereGeometry args={[0.04, 6, 6]} />
          <meshStandardMaterial color="#7CFC00" roughness={0.6} />
        </mesh>
        <mesh position={[-0.03, 0.12, -0.01]}>
          <sphereGeometry args={[0.035, 6, 6]} />
          <meshStandardMaterial color="#66CD00" roughness={0.6} />
        </mesh>
        <mesh position={[0.04, 0.09, -0.03]}>
          <sphereGeometry args={[0.03, 6, 6]} />
          <meshStandardMaterial color="#7CCD7C" roughness={0.6} />
        </mesh>
      </group>

      {/* ===== 2. 马克杯 — 放在中间靠前 ===== */}
      <group position={[0.1, 0, -0.2]}>
        {/* 杯身 */}
        <mesh position={[0, 0.04, 0]}>
          <cylinderGeometry args={[0.05, 0.045, 0.08, 8]} />
          <meshStandardMaterial color={color} roughness={0.5} />
        </mesh>
        {/* 把手 */}
        <mesh position={[0.06, 0.04, 0]}>
          <torusGeometry args={[0.03, 0.01, 6, 8, Math.PI]} />
          <meshStandardMaterial color={color} roughness={0.5} />
        </mesh>
        {/* 杯内咖啡 */}
        <mesh position={[0, 0.08, 0]}>
          <cylinderGeometry args={[0.04, 0.04, 0.01, 8]} />
          <meshStandardMaterial color="#3E2723" roughness={0.8} />
        </mesh>
        {/* 热气（两个小半透明球） */}
        <mesh position={[0.02, 0.11, 0]}>
          <sphereGeometry args={[0.015, 6, 6]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} transparent opacity={0.4} />
        </mesh>
        <mesh position={[-0.01, 0.14, 0.01]}>
          <sphereGeometry args={[0.012, 6, 6]} />
          <meshStandardMaterial color="#ffffff" roughness={0.2} transparent opacity={0.3} />
        </mesh>
      </group>

      {/* ===== 3. 笔筒 — 侧翼前方，不挡键盘 ===== */}
      <group position={[-0, 0, -0.38]}>
        {/* 筒身 */}
        <mesh position={[0, 0.05, 0]}>
          <cylinderGeometry args={[0.06, 0.06, 0.1, 8]} />
          <meshStandardMaterial color="#F5F0E8" roughness={0.7} />
        </mesh>
        {/* 笔1（主题色） */}
        <mesh position={[-0.02, 0.11, 0.01]} rotation={[0.1, 0, 0.15]}>
          <cylinderGeometry args={[0.01, 0.01, 0.08, 6]} />
          <meshStandardMaterial color={color} roughness={0.5} />
        </mesh>
        {/* 笔2（灰色） */}
        <mesh position={[0.02, 0.12, -0.01]} rotation={[0.05, 0, -0.1]}>
          <cylinderGeometry args={[0.01, 0.01, 0.08, 6]} />
          <meshStandardMaterial color="#888888" roughness={0.5} />
        </mesh>
        {/* 笔3（黑色） */}
        <mesh position={[0, 0.13, -0.02]} rotation={[-0.05, 0.1, 0.05]}>
          <cylinderGeometry args={[0.01, 0.01, 0.08, 6]} />
          <meshStandardMaterial color="#333333" roughness={0.5} />
        </mesh>
      </group>

      {/* ===== 4. 散落文件 — 放在侧翼前侧 ===== */}
      <group position={[-0.55, 0, 0.3]}>
        {/* 文件1 — 水平放置 */}
        <mesh position={[0, 0.005, 0]} rotation={[0, 0.2, 0]}>
          <boxGeometry args={[0.15, 0.01, 0.1]} />
          <meshStandardMaterial color="#FFFFFF" roughness={0.8} />
        </mesh>
        {/* 文件2 — 倾斜叠放 */}
        <mesh position={[0.04, 0.012, 0.02]} rotation={[0, -0.15, 0]}>
          <boxGeometry args={[0.14, 0.01, 0.09]} />
          <meshStandardMaterial color="#F8F8F8" roughness={0.8} />
        </mesh>
        {/* 文件上的彩色便签 */}
        <mesh position={[0.06, 0.018, -0.02]} rotation={[0, 0, 0]}>
          <planeGeometry args={[0.03, 0.03]} />
          <meshBasicMaterial color={color} />
        </mesh>
      </group>
    </group>
  )
}