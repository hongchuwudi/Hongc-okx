/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: CameraControls 组件 Props 类型
 */

export interface CameraControlsProps {
  /** 当前是否允许自由旋转 */
  rotateEnabled: boolean
  /** 点击自由旋转按钮时的回调函数，用于切换旋转状态 */
  onToggleRotate: () => void
  /** 点击归正视角按钮时的回调函数，用于将相机重置到初始视角 */
  onResetView: () => void
}
