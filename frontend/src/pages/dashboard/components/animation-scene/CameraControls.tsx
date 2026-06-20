/**
 * 创建时间: 2026-06-13
 * 作者: hongchuwudi
 * 描述: 相机控制按钮组 — 右上角自由旋转切换 + 归正视角
 */

import { RotateCw, Maximize } from 'lucide-react'
import type { CameraControlsProps } from '@/types/CameraControls'

/**
 * 相机控制按钮组
 * 通常浮动在 3D 场景的右上角，提供旋转模式切换和视角重置功能。
 */
export default function CameraControls({
  rotateEnabled,
  onToggleRotate,
  onResetView,
}: CameraControlsProps) {
  return (
    <div className="absolute top-3 right-3 flex gap-2 z-10">
      <button
        onClick={onToggleRotate}
        className={`btn btn-md btn-circle border-0 shadow-md backdrop-blur
          ${
            rotateEnabled
              ? 'bg-primary text-primary-content'
              : 'bg-base-100/80 text-base-content hover:bg-base-100'
          }`}
        title={rotateEnabled ? '锁定旋转' : '自由旋转'}
      >
        <RotateCw className="w-5 h-5" />
      </button>

      <button
        onClick={onResetView}
        className="btn btn-md btn-circle bg-base-100/80 border-0 shadow-md backdrop-blur text-base-content hover:bg-base-100"
        title="归正视角"
      >
        <Maximize className="w-5 h-5" />
      </button>
    </div>
  )
}
