/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 3D 动画场景接口定义
 *
 * 包含:
 * - 接口: CubicleProps — 卡通格子间 Props
 */

// 卡通格子间
export interface CubicleProps {
  gx: number
  gy: number
  color: string
  flip?: boolean
  chairOffset?: [number, number, number] // 
  chairRotationY?: number   // 椅子绕Y轴旋转角度（弧度）
}
