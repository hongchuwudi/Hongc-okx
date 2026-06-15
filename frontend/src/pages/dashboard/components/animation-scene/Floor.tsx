/**
 * 创建时间: 2026-06-12
 * 作者: hongchuwudi
 * 描述: 棋盘格地板 — 40x40 交替色砖块，颜色跟随主题切换
 */

import { useThemeStore } from '@/stores/themeStore'
import { GRID as GRID_SIZE, TILE } from './constants'

/** 主题对应的地板颜色 [浅色, 深色] */
const FLOOR_COLORS: Record<string, [string, string]> = {
  light: ['#e8e8ec', '#d4d4d8'],
  dark:  ['#1f1f3a', '#141425'],
}

export default function Floor() {
  const theme = useThemeStore(s => s.theme)
  const [colorA, colorB] = FLOOR_COLORS[theme.id] ?? FLOOR_COLORS.dark
  const tiles: JSX.Element[] = []

  for (let row = 0; row < GRID_SIZE; row++) {
    for (let col = 0; col < GRID_SIZE; col++) {
      const x = (col - GRID_SIZE / 2 + 0.5) * TILE
      const z = (row - GRID_SIZE / 2 + 0.5) * TILE
      const isDark = (row + col) % 2 === 0

      tiles.push(
        <mesh
          key={`${row}-${col}`}
          position={[x, 0, z]}
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <planeGeometry args={[TILE, TILE]} />
          <meshStandardMaterial
            color={isDark ? colorB : colorA}
            roughness={0.8}
          />
        </mesh>
      )
    }
  }

  return <group>{tiles}</group>
}
