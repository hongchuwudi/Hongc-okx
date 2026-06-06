# BTC/USDT 永续合约自动交易系统

基于 AI 大模型的 BTC/USDT 永续合约自动交易机器人，集成 React Web 实时监控面板。

## 架构概览

```
run.py                  统一启动入口（FastAPI + 交易引擎）
app/                    后端核心
  config.py             统一配置（.env → dataclass）
  database.py           PostgreSQL + Redis 连接管理
  logger.py             日志模块
  engine/loop.py        交易引擎主循环（事件驱动）
  exchange/client.py    OKX 交易所客户端
  models/                SQLAlchemy ORM 模型
  services/             服务层（行情/风控/调度/策略/交易）
  strategies/           策略实现（DeepSeek AI + 技术指标）
  api/                  FastAPI v2.0 + WebSocket 实时推送
frontend/               React 18 + TypeScript + Vite + Recharts
  src/                  源码
  dist/                 生产构建产物
legacy/                 v1.0 归档（Streamlit 单体架构，仅供参考）
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env_template .env
# 编辑 .env 填入 API 密钥和数据库连接信息

# 启动系统（API + 交易引擎）
python run.py
```

- API 地址: `http://127.0.0.1:8765`
- WebSocket: `ws://127.0.0.1:8765/ws/live`
- API 文档: `http://127.0.0.1:8765/docs`

### 前端开发

```bash
cd frontend
npm install
npm run dev        # Vite 开发服务器 http://localhost:5173
npm run build      # 生产构建 → dist/
```

## 环境配置

### .env 配置项

```env
# AI 模型
AI_PROVIDER=deepseek           # deepseek 或 qwen
DEEPSEEK_API_KEY=your_key
DASHSCOPE_API_KEY=your_key

# OKX 交易所
OKX_API_KEY=your_key
OKX_SECRET=your_secret
OKX_PASSWORD=your_passphrase
OKX_SANDBOX=true               # true=模拟盘, false=实盘

# 代理（国内服务器需要）
HTTPS_PROXY=http://127.0.0.1:7897

# PostgreSQL
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=root
POSTGRES_PASSWORD=your_password
POSTGRES_DB=trading

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=12

# 风控
MAX_DAILY_DRAWDOWN_PCT=10.0
MAX_DAILY_LOSS_USDT=50.0
```

## 交易逻辑

- **周期**: 每 60 秒一个 tick，整点对齐
- **数据**: 1h K 线 × 168 根（7 天）
- **AI**: DeepSeek 分析 OHLCV + 技术指标 + 市场情绪 → 生成 BUY/SELL/HOLD 信号
- **验证**: RSI/趋势/MACD 交叉验证，信号冲突时降级或翻转为 HOLD
- **风控**: 日回撤熔断、日亏损限额、仓位上限
- **执行**: OKX 算法止盈止损委托单，ATR 动态止损 + 移动止盈

## 注意事项

- 首次运行前务必在 OKX 设置为**单向持仓**和**全仓保证金**模式
- 建议先使用 OKX 模拟盘测试（`OKX_SANDBOX=true`）
- 国内服务器需配置代理才能访问 OKX API
- 需要 PostgreSQL + Redis 运行中

## v1.0 归档

旧版 Streamlit 单体架构代码已归档至 `legacy/`，详见 `legacy/README.md`。
