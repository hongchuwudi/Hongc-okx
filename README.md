# Hongc-OKX — AI 永续合约自动交易系统

基于 **5 Agent Swarm** 协作流水线的 DOGE/USDT 永续合约 AI 自动交易系统，集成 React 3D 实时驾驶舱。

## 架构概览

```
run.py                       统一启动入口（FastAPI + 交易引擎）
app/                         后端核心
  agents/                    5 Agent Swarm 决策引擎
    coordinators/            协调器（5/3/1 Agent 策略模式）
    models/                  独立 LLM 实例（DeepSeek/Qwen）
    prompts/                 角色系统提示词
    toolkits/                工具集三层架构（计算/胶水/消费）
  engine/loop.py             交易引擎主循环（事件驱动）
  exchange/client.py         OKX 交易所门面（ccxt + 代理切换）
  services/                  服务层（行情/交易/风控/调度/回测/仪表盘）
  api/v1/                    FastAPI 版本化路由 + WebSocket
  entities/                  SQLAlchemy ORM 模型
  schemas/                   Pydantic 请求/响应模型
  config/                    配置模块（AI/OKX/Trade 独立 dataclass）
  database/                  PostgreSQL + Redis 连接管理
  core/                      日志 + 异常体系
frontend/                    React 18 + TypeScript + daisyUI 5 + Three.js
  src/pages/dashboard/       3D 场景实时驾驶舱
  src/components/common/     通用组件（Paginator/FormInput 等）
```

## 快速开始

```bash
cd backend
pip install -r requirements.txt
cp .env_template .env          # 编辑 .env 填入 API 密钥
python run.py                  # 启动 API + 交易引擎
```

```bash
cd frontend
npm install && npm run dev     # Vite 开发服务器 :5173
```

- API: `http://127.0.0.1:8765` | 文档: `http://127.0.0.1:8765/docs`
- WebSocket: `ws://127.0.0.1:8765/ws/live`

## Agent 流水线

```
调度师 → 分析师 ∥ 复盘师 → 风控师 → 交易裁决员
         ↑ asyncio.gather 并行 ↑    ↑ 可退回重做(2次) ↑
```

- **5 Agent Swarm** — 完整深度推理，每个 Agent 拥有独立 LLM + 工具集 + 私有记忆
- **3 Agent 快速模式** — Super-Analyst 合并分析+复盘，缩短链路
- **1 Agent 急速模式** — 预计算全部指标注入，跳过工具调用，仅查历史即决策
- **tech 纯规则** — AI 连续失败自动降级，保证极端情况不中断

Agent 间通过 `transfer_to_X`（控制权移交）和 `ask_X`（对话询问）实现双向通信。

## 配置

主要运行时配置（前端或 Redis 实时修改，下个 tick 生效）：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `TRADE_SYMBOL` | DOGE/USDT:USDT | 交易对 |
| `TRADE_LEVERAGE` | 10 | 杠杆倍数 |
| `AGENT_MODE` | 5_agent | 5_agent / 3_agent / 1_agent / tech |
| `AGENT_AUTO_START` | true | 启动后自动运行引擎 |
| `tick_interval_seconds` | 120 | Tick 间隔（秒） |
| `order_amount` | 1.0 | 单笔保证金（USDT） |
| `max_daily_drawdown_pct` | 10.0 | 日回撤熔断阈值 |
| `max_daily_loss_usdt` | 50.0 | 日亏损限额 |

完整配置见 `backend/.env_template`。

## 特性

- **私有记忆学习闭环** — 预测→执行→反馈→学习，PostgreSQL 持久化，DB 不可用自动降级
- **多层安全兜底** — 风控师 go_no_go 硬门禁 + LLM 输出三层解析 + 连续失败自动熔断
- **动态持仓管理** — 每个 Tick 更新追踪止损（持仓观望时同样执行），ATR 自适应止盈
- **WebSocket 实时推送** — Redis Pub/Sub 驱动，前端 3D 场景 + ECharts 图表
- **策略模式热切换** — 运行时切换 5/3/1 Agent 模式，无需重启
- **OKX 算法单** — 止盈止损委托挂在 OKX 服务端，程序崩溃也能触发

## 注意事项

- 首次运行前在 OKX 设置为**单向持仓 + 全仓保证金**模式
- 建议先用模拟盘测试（`OKX_SANDBOX=true`）
- 国内服务器需配置 `HTTPS_PROXY` 代理
- 需要 PostgreSQL + Redis 运行中
- 提交前检查 `.env` 已在 `.gitignore` 中排除
