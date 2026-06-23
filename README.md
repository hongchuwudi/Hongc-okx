# Hongc-OKX — AI 永续合约自动交易系统

基于 **5 Agent Swarm** 协作流水线的 OKX 永续合约 AI 自动交易系统，集成 React 3D 实时驾驶舱。

- **AI 决策**:5/3/1 Agent 三档模式 + tech 纯规则降级,DeepSeek V4-Flash 驱动
- **交易标的**:OKX 永续合约,默认 DOGE/USDT:USDT,全仓 + 单向持仓,10x 杠杆
- **实时可视化**:React 18 + Three.js 3D 场景 + ECharts 图表,WebSocket 推送
- **安全兜底**:风控硬门禁 + 连续失败熔断 + AI 余额不足自动降级 + OKX 服务端算法止盈止损

## 架构概览

```
backend/
  run.py                       统一启动入口（FastAPI + 交易引擎）
  app/
    agents/                    AI 决策引擎（仅内部使用，外部经 services/agent/ 访问）
      coordinators/            协调器（5/3/1 Agent 三种策略模式）
      models/                  独立 LLM 实例（DeepSeek/Qwen，按角色独立配置）
      prompts/                 角色系统提示词
      toolkits/                工具集三层架构（计算层 / 胶水层 / 消费层）
      parser.py                LLM 输出三层兜底解析（JSON → 表格 → KV）
    engine/                    交易引擎主循环（8 步 tick 流水线）
      loop/                    tick 各步骤实现（行情/策略/持仓/记忆/风控/交易/持久化）
      runtime/                 运行时配置热同步（Redis → 引擎）
    services/                  全部业务逻辑（行情/交易/风控/调度/回测/仪表盘/Agent）
    exchange/                  OKX 交易所门面（ccxt + 主备代理切换）
    api/v1/                    FastAPI 版本化路由 + WebSocket
    entities/                  SQLAlchemy ORM 模型（纯数据容器）
    schemas/                   Pydantic 请求/响应模型
    core/                      配置 / 数据库 / 日志 / 异常体系
  tests/                       unit + integration 测试（pytest + pytest-asyncio）
  pytest.ini                   pytest-asyncio 配置（session 级 event loop）
frontend/
  src/pages/dashboard/         3D 场景实时驾驶舱
  src/components/              跨页面复用公共组件
  src/api/                     后端 API 请求统一收口
  src/types/                   TypeScript 类型定义
```

**分层调用链**:`api/v1/ → services/ → agents/ | entities/ | exchange/ | Redis`

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env            # 编辑 .env 填入 OKX / DeepSeek / PG / Redis 密钥
python run.py                   # 启动 API + 交易引擎
```

### 前端

```bash
cd frontend
npm install
npm run dev                     # Vite 开发服务器 :5173
```

- API:`http://127.0.0.1:8765` | 文档:`http://127.0.0.1:8765/docs`
- WebSocket:`ws://127.0.0.1:8765/ws/live`

### 前置依赖

- PostgreSQL + Redis 运行中
- Python 3.12 + Node 18+
- 国内网络环境需配置 `HTTPS_PROXY` 代理访问 OKX / DeepSeek

## Agent 流水线

```
调度师 → 分析师 ∥ 复盘师 → 风控师 → 交易裁决员
         ↑ asyncio.gather 并行 ↑    ↑ 可退回重做（最多 2 次）↑
```

| 模式 | 说明 | 适用场景 |
|---|---|---|
| **5 Agent Swarm** | 完整深度推理,每个 Agent 独立 LLM + 工具集 + 私有记忆 | 复杂行情,追求决策质量 |
| **3 Agent 快速** | Super-Analyst 合并分析 + 复盘,缩短链路 | 平衡速度与质量 |
| **1 Agent Solo** | 预计算全部指标注入,跳过工具调用,仅查历史即决策 | 急速模式,低延迟 |
| **tech 纯规则** | 不调用 AI,纯技术指标 5 信号打分决策 | AI 不可用 / 余额不足降级 |

Agent 间通过 `transfer_to_X`(控制权移交)和 `ask_X`(对话询问)实现双向通信。

### AI 降级链路

1. **余额不足降级** — 每 tick 查询 DeepSeek 余额,低于 0.05 CNY 时本 tick 直接走技术指标,不调用 Agent(避免 402 失败)
2. **AI 调用失败降级** — Agent 抛异常时降级为技术指标,连续失败 5 次暂停冷却,10 次停止引擎
3. **tech 纯规则兜底** — 极端情况下保证不中断

## 配置

主要运行时配置(前端或 Redis 实时修改,下个 tick 生效):

| 参数 | 默认值 | 说明 |
|---|---|---|
| `TRADE_SYMBOL` | DOGE/USDT:USDT | 交易对 |
| `TRADE_LEVERAGE` | 10 | 杠杆倍数 |
| `AGENT_MODE` | 5_agent | 5_agent / 3_agent / 1_agent / tech |
| `AGENT_AUTO_START` | true | 启动后自动运行引擎 |
| `tick_interval_seconds` | 120 | Tick 间隔(秒) |
| `order_amount` | 1.0 | 单笔保证金(USDT) |
| `max_daily_drawdown_pct` | 10.0 | 日回撤熔断阈值(%) |
| `max_daily_loss_usdt` | 50.0 | 日亏损限额(USDT) |

完整配置见 `backend/.env.example`。AI 余额与降级状态可查 `GET /api/v1/config/ai-balance`。

## 特性

- **私有记忆学习闭环** — 预测 → 执行 → 反馈 → 学习,PostgreSQL 持久化,DB 不可用自动降级
- **多层安全兜底** — 风控师 go_no_go 硬门禁 + LLM 输出三层解析 + 信号归一化 + 连续失败熔断
- **动态持仓管理** — 每个 tick 更新追踪止损(HOLD tick 同样执行),ATR 自适应止盈宽度
- **WebSocket 实时推送** — Redis Pub/Sub 驱动,前端 3D 场景 + ECharts 图表实时更新
- **策略模式热切换** — 运行时切换 5/3/1 Agent 模式,无需重启
- **OKX 算法单** — 止盈止损委托挂在 OKX 服务端,程序崩溃也能触发
- **AI 余额监控** — 实时查询 DeepSeek 余额,不足自动降级,避免无效调用

## 测试

```bash
cd backend
python -m pytest tests/unit -q              # 单元测试
python -m pytest tests/integration -q       # 集成测试（需 PG + Redis + .env）
python -m pytest tests/integration/services # service 层集成（真实 Redis）
```

- 单元测试全 mock,不依赖外部服务
- 集成测试真实连 Redis / PostgreSQL,`pytest.ini` 配 session 级 event loop 避免跨测试连接池冲突
- `tests/integration/agents/` 依赖真实 LLM,余额不足时自动跳过

## 注意事项

- 首次运行前在 OKX 设置为**单向持仓 + 全仓保证金**模式
- 建议先用模拟盘测试(`OKX_SANDBOX=true`)
- 国内服务器需配置 `HTTPS_PROXY` 代理
- `backend/.env` 已加入 `.gitignore`,包含真实密钥,绝对禁止提交
