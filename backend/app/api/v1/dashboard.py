"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: dashboard.py 仪表盘API路由
描述: 仪表盘 API — 提供系统状态、健康检查、权益曲线和 K 线数据接口

包含:
- 端点: GET /api/health — 数据库连接健康检查
- 端点: GET /api/status — 系统完整运行状态（账户/持仓/AI信号/风控/绩效）
- 端点: GET /api/equity — 历史权益曲线数据（?limit=500）
- 端点: GET /api/kline — K 线 OHLCV 数据（?symbol=&timeframe=&limit=100）
"""

from fastapi import APIRouter, Query

from app.services.dashboard.dashboard import dashboard_service
from app.schemas.responses.common import HealthResponse
from app.schemas.responses.dashboard import StatusResponse, EquityPoint, KlinePoint, MarketInfo

router = APIRouter(prefix="/api/v1")


# === 健康检查 =================================================================

# 数据库连接健康检查 — 执行 SELECT 1 验证 PostgreSQL 连通性
@router.get("/health", response_model=HealthResponse)
def health():
    return dashboard_service.check_health()


# === 系统状态 =================================================================

# 系统完整运行状态 — 包含账户余额/权益/杠杆、BTC 行情、当前持仓、
# AI 信号（方向/置信度/理由/止盈止损）、交易绩效（总盈亏/胜率/交易数）、止损止盈订单
@router.get("/status", response_model=StatusResponse)
def api_get_status():
    return dashboard_service.get_status()


# === 权益曲线 =================================================================

# 历史权益曲线数据 — 返回 [{timestamp, equity}, ...]，
# ?limit=500 控制数据点数量（1-2000），供前端 ECharts 绘制权益走势图
@router.get("/equity", response_model=list[EquityPoint])
def api_get_equity(limit: int = Query(500, ge=1, le=2000)):
    return dashboard_service.get_equity_curve(limit)


# === K 线数据 ==================================================================

# K 线 OHLCV 数据 — 从 OKX 拉取历史 K 线供前端渲染蜡烛图，
# 参数: ?symbol=BTC/USDT:USDT&timeframe=1h&limit=100
@router.get("/kline", response_model=list[KlinePoint])
def api_get_kline(
    symbol: str = Query("BTC/USDT:USDT"),
    timeframe: str = Query("1h"),
    limit: int = Query(100, ge=1, le=500),
):
    return dashboard_service.get_kline_data(symbol, timeframe, limit)


# === 引擎开关 ==================================================================

@router.get("/engine")
def api_engine_status():
    from app.services.engine.engine_control import get_status
    return get_status()


@router.post("/engine/start")
async def api_engine_start():
    from app.services.engine.engine_control import start
    await start()
    return {"ok": True, "message": "引擎已启动"}


@router.post("/engine/stop")
async def api_engine_stop():
    from app.services.engine.engine_control import stop
    await stop()
    return {"ok": True, "message": "引擎已停止"}


@router.post("/engine/reset-circuit")
async def api_reset_circuit():
    from app.services.risk.risk import risk_service
    await risk_service.reset_circuit_breaker()
    return {"ok": True, "message": "熔断已重置"}


# === Agent 日志 ===============================================================

@router.get("/agents/logs")
async def api_agent_logs(limit: int = Query(5, ge=1, le=10)):
    from app.agents.agent_status import get_recent_agent_logs
    return await get_recent_agent_logs(limit)


@router.get("/agents/logs/paginated")
async def api_agent_logs_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    mode: str = Query("", description="按模式过滤"),
):
    from app.agents.agent_status import get_agent_logs_paginated
    return await get_agent_logs_paginated(page, page_size)


# === WS 测试 ==================================================================

@router.post("/ws-test")
def api_ws_test():
    from app.services.backtest.backtest_service import _push_sync
    _push_sync({"type": "backtest_done", "run_id": -1, "trades_count": 0})
    return {"ok": True, "msg": "sent"}
