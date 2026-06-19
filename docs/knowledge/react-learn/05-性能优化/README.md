# 05 性能优化

**状态：○ 待学习**

## 知识点

- [ ] 什么时候需要优化（先量再治）
- [ ] `React.memo` — 跳过不必要的重渲染
- [ ] `useMemo` / `useCallback` — 你已在用
- [ ] `useTransition` — 标记低优先级更新
- [ ] `useDeferredValue` — 延迟更新值
- [ ] `lazy` + `Suspense` — 代码分割
- [ ] React Compiler（React 19）— 自动 memo
- [ ] 虚拟滚动（`react-window`）
- [ ] 渲染次数分析（React DevTools Profiler）

## 项目中的潜在优化点

- 交易记录列表 > 200 条时用虚拟滚动
- Agent 日志流可以用 `useTransition` 避免阻塞
- 大组件可以 `lazy` 懒加载

## 常见面试题

- React.memo 的浅比较原理？
- useCallback 真的能提高性能吗？什么时候适得其反？
- React Compiler 做了什么？
