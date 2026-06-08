# CLAUDE.md

**语言偏好：请始终使用中文回复用户。**

## 项目概述

OKX 永续合约 AI 自动交易系统。5 Agent Swarm + DeepSeek V4-Flash + React。默认交易对：DOGE/USDT:USDT，10x 杠杆，6 分钟 tick。

## 常用命令

```bash
cd backend && pip install -r requirements.txt    # 安装依赖
cd backend && cp .env_template .env              # 配置环境变量
cd backend && python run.py                      # 启动后端（API + 引擎）
cd frontend && npm install && npm run dev        # 启动前端 :5173
cd backend && python tests/run_tests.py          # 运行测试
cd backend && python tests/run_tests.py --quick  # 快速测试
```

## 分层架构（核心规则）

```
api/v1/     →  纯声明层：路由 + 参数 + 文档 + 调用 service。无业务逻辑、无数据库查询
services/   →  全部业务逻辑，统一类 + 全局单例。可调用 ORM、Redis、OKX
agents/     →  AI 决策引擎，仅内部使用。外部只能通过 services/agent/ 访问
engine/     →  主循环编排，只调用 services，绝不直接操作数据库或 Redis
entities/   →  SQLAlchemy ORM 模型，纯数据容器，零业务逻辑
schemas/    →  Pydantic 请求/响应模型
exchange/   →  OKX API 封装（基于 ccxt）
```

**调用链**：`api/v1/ → services/ → agents/ | entities/ | exchange/ | Redis`

## 异常体系

```
AppError(500) → NotFoundError(404) / BusinessError(400) / ExternalServiceError(502) / ConfigError(500)
```

Service 层直接 `raise NotFoundError(...)`，禁止 `return {"ok": false}`。全局异常处理器在 `main.py` 中自动转换为 JSON 响应。

## 核心模式

- **5 Agent 流水线**：调度师 → 分析师∥复盘师（asyncio.gather 并行）→ 风控师（可退回重做，最多 2 次）→ 交易裁决员。每个 Agent 是独立的 LangGraph ReAct Agent（专用 LLM + 工具集 + ReAct 循环），通过 `transfer_to_X` / `ask_X` 进行移交和对话。
- **API 版本管理**：所有接口统一在 `/api/v1/` 前缀下。未来 v2 新建 `api/v2/`，不影响 v1。
- **配置注入**：生产代码使用 `from app.config import config` 全局单例。测试代码使用 `get_config(trade=TradeConfig(symbol="ETH/USDT:USDT"))` 按需覆盖。
- **OKX 交易模式**：全仓模式 + 单向持仓 + 永续合约。通过代理访问（国内网络环境必须）。
- **数据持久化**：每次 tick 写入 PostgreSQL（SystemStatus/Trade/EquitySnapshot）+ Redis 缓存 + Pub/Sub 推送。
- **动态持仓管理**：PositionManager 每个 tick 更新追踪止损（含 HOLD tick），ATR 自适应调整止盈止损宽度。

## 命名规范

### 文件命名（Python）

格式 `{模块}_{功能描述}.py`，前缀 = 模块名，全英文单词，禁止缩写。

```
toolkit_calc_rsi.py   ✓ 正确
tk_data.py            ✗ 禁止缩写
data.py               ✗ 缺少模块前缀
```

### 目录命名

全英文单词。子模块实现在 `tools/` 子目录中。胶水层代码放在模块根目录。

### 代码命名

- 函数：`snake_case`
- 类：`PascalCase`
- 常量：`UPPER_SNAKE`
- 私有：`_` 前缀

## 工具集三层架构（强制）

```
toolkit_calc_*.py    ← 纯计算层：只导入 pandas/numpy/toolkit_data，返回 str
toolkit_*.py         ← 胶水层：只导入 lc_tool + 计算函数，不含计算逻辑
coordinator.py       ← 消费层：导入工具 → create_react_agent(tools=[...])
```

新增工具流程：`在计算层添加函数 → 在胶水层用 lc_tool() 包装 → 传入 coordinator`

## 注释规范

### Python 文件头

```python
"""
创建时间: YYYY-MM-DD
作者: hongchuwudi
描述: <一句话说明文件职责>

包含:
- 类: 类名 — 一句话说明
- 函数: 函数名 — 一句话说明
"""
```

### TypeScript 文件头

```tsx
/**
 * 创建时间: YYYY-MM-DD
 * 作者: hongchuwudi
 * 描述: <一句话说明文件职责>
 *
 * 包含:
 * - 组件: 组件名 — 一句话说明
 * - Hook: useHook — 一句话说明
 */
```

### 行内注释

Python：`#` 在定义前 = 说明"做什么"。在逻辑内部 = 说明"为什么"。
TypeScript：`//` 在定义前。

## 前端开发规范（强制）

### 目录结构

```
src/
  types/         → 所有 TypeScript interface 类型定义
  types/props/   → 所有组件 Props 接口 + API 通信类型
  pages/         → 所有页面模块，每个模块一个目录
  pages/XXXX/components/ → 页面模块内部的子组件
  components/    → 所有跨页面复用的公共组件
  api/           → 所有后端 API 请求函数，统一收口
  constants/       → 所有常量数据存放在这里
```

### 编码规则

1. **虚拟滚动** — 大列表必须使用 react-window，禁止直接渲染全部数据。
2. **组件规范** — 函数组件 + TypeScript Props 接口。一个文件只做一件事。
3. **命名规范** — 全英文单词，禁止缩写。文件头必须包含作者和创建日期。
4. **API 封装** — 请求统一收口在 api/ 层。组件禁止直接调用 fetch。
5. **类型分离** — 类型定义在 types/ 目录，组件 Props 放在 types/props/。优先使用 interface，禁止无理由使用 `any`。
6. **Tailwind 优先** — 避免内联样式。优先使用 Flex/Grid 布局。响应式设计。
7. **Hook 规范** — 命名以 `use` 为前缀，只处理状态和副作用，不与 JSX 耦合，必须清理副作用。
8. **性能优化** — 展示型组件使用 React.memo。WebSocket 连接作为全局单例共享。
9. **错误处理** — API 封装函数返回 Promise。统一错误处理，组件中禁止重复 try/catch。
10. **提交自检** — 提交前对照全部规范自查，不合规代码禁止提交。

## 硬性规则

- **严禁使用 emoji** — 任何地方（print、logger、注释、字符串、文件内容）都不允许出现 emoji。Windows GBK 编码会直接崩溃。用纯文本替代。
- `print()` 只允许在 `run.py` 等入口脚本中使用，库代码统一用 `logger`。

## 安全

- `backend/.env` 已加入 `.gitignore`，包含真实 API 密钥，绝对禁止提交到版本控制。
