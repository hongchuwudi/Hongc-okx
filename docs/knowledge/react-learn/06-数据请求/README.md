# 06 数据请求

**状态：★ 基本掌握 / ○ TanStack Query 待学习**

## 知识点

- [ ] `fetch` + Promise — 你已在用
- [ ] SSE（Server-Sent Events）— 流式数据
- [ ] WebSocket — 全双工实时推送
- [ ] 请求重试 + 超时
- [ ] 乐观更新（先改 UI，后确认）
- [ ] TanStack Query — 缓存/去重/重试/后台刷新

## 项目中的例子

- `api/` 层 — fetch 封装，get/post/put/del
- `utils/request.ts` — 拦截器，统一错误处理
- `api/backtest.ts` — SSE 流式消费（`runBacktestStream`）
- `utils/ws.ts` — WebSocket 全局单例

## 为什么该学 TanStack Query

你现在每个组件手动管理 loading/error/data 三态 + 依赖数组 + 清理定时器。TanStack Query 把这些自动化了：

```ts
// 你现在的写法 —— 10 行
const [data, setData] = useState([])
const [loading, setLoading] = useState(true)
useEffect(() => { fetch().then(setData).finally(() => setLoading(false)) }, [])

// TanStack Query —— 1 行
const { data, isLoading } = useQuery({ queryKey: ['kline'], queryFn: fetchKline })
```

## 常见面试题

- SSE 和 WebSocket 选型标准？
- 乐观更新是什么？怎么回滚？
- TanStack Query 的缓存策略？
