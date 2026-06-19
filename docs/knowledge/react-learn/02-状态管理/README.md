# 02 状态管理

**状态：★ 已掌握**

## 知识点

- [ ] `useState` — 组件内部状态
- [ ] `useReducer` — 复杂状态逻辑
- [ ] `useContext` — 跨组件传递
- [ ] Zustand — 全局状态（你项目的主力方案）
- [ ] 状态提升 — 父子组件共享
- [ ] 状态放在哪里的决策树

## 项目中的例子

- `stores/dashboardStore.ts` — Zustand，全局仪表盘状态
- `context/DashboardContext.tsx` — useReducer，状态机模式（LOADING/OK/ERROR/TICK）
- `pages/trades/index.tsx` — useState，页面级状态

## 常见面试题

- Redux 和 Zustand 的区别？
- Context 适合做什么，不适合做什么？
- 什么时候该用 useReducer 而不是 useState？
