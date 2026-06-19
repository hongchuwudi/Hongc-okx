# 03 副作用

**状态：★ 已掌握**

## 知识点

- [ ] `useEffect` — 管理副作用
- [ ] 依赖数组（`deps`）的规则
- [ ] 清理函数（`return () => cleanup()`）
- [ ] `useCallback` — 稳定函数引用
- [ ] `useMemo` — 缓存计算结果
- [ ] `useRef` — 持有不触发重渲染的值
- [ ] 自定义 Hook — 组合上述所有

## 项目中的例子

- `hooks/usePolling.ts` — useRef + useEffect 组合
- `hooks/useAutoScroll.ts` — useRef + useEffect + useCallback 组合
- `pages/dashboard/components/KlineCard.tsx` — useMemo 缓存 ECharts option

## 常见面试题

- useEffect 的执行时机？
- 空 deps 数组、有 deps、无 deps 的区别？
- 为什么 useCallback 里的 state 是旧值？怎么解决？
