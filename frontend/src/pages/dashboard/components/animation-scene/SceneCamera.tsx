/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 摄像机控制 — 自由旋转/平移/缩放 + 归正
 */

import { useEffect, useRef } from 'react'
import { useThree } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'

interface Props {
  rotateEnabled: boolean
  resetKey: number
}

const DEFAULT = { pos: [3, 11, 10] as const, target: [0, 0, 0] as const }

export default function SceneCamera({ rotateEnabled, resetKey }: Props) {
  const controlsRef = useRef<OrbitControlsImpl>(null)
  const { camera } = useThree()

  // 归正视角
  useEffect(() => {
    if (resetKey === 0) return
    const ctrl = controlsRef.current
    if (!ctrl) return
    camera.position.set(...DEFAULT.pos)
    ctrl.target.set(...DEFAULT.target)
    ctrl.update()
  }, [resetKey, camera])

  return (
    <OrbitControls
      ref={controlsRef}
      enableRotate={rotateEnabled}
      enablePan={true}
      enableZoom={true}
      minZoom={3}
      maxZoom={20}
      target={DEFAULT.target}
      mouseButtons={
        rotateEnabled
          ? { LEFT: 0, MIDDLE: 1, RIGHT: 2 }   // 标准：左键旋转，中键缩放，右键平移
          : { LEFT: 2, MIDDLE: 1, RIGHT: 2 }    // 锁定旋转：左键/右键平移
      }
    />
  )
}
