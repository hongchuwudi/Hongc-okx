/**
 * 创建时间: 2026-06-14
 * 作者: hongchuwudi
 * 描述: 回测K线图的缩放选项常量
 */

// K线图缩放比例选项
export const ZOOM_LEVELS = [
    { label: '全部', start: 0, end: 100 },
    { label: '75%', start: 25, end: 100 },
    { label: '50%', start: 50, end: 100 },
    { label: '25%', start: 75, end: 100},
    { label: '10%', start: 45 + 45, end: 100},
] as const