"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: backtest.py 回测API路由
描述: 回测 API — 提供回测触发执行、历史列表和详情查询接口

包含:
- 端点: POST /api/backtest/run — 触发一次回测（同步执行，返回结果）
- 端点: POST /api/backtest/run-stream — 流式回测（SSE，逐 K 线推送）
- 端点: POST /api/backtest/run-async — 异步回测（WebSocket 推送）
- 端点: GET /api/backtest/runs — 历史回测记录列表
- 端点: GET /api/backtest/runs/{run_id} — 单次回测完整详情
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.schemas.requests.backtest import RunRequest
from app.services.backtest.backtest_service import backtest_service

router = APIRouter(prefix="/api/v1/backtest")


# 触发一次回测 — 同步执行，等待完成后返回完整结果
@router.post("/run")
def start_backtest(req: RunRequest):
    return backtest_service.run(
        strategy=req.strategy, symbol=req.symbol, timeframe=req.timeframe,
        initial_capital=req.initial_capital, position_ratio=req.position_ratio,
        fee_rate=req.fee_rate, warmup=req.warmup, data_limit=req.data_limit,
        temperature=req.temperature,
    )


# K线预览 — 返回 OHLCV 原始数据，供前端画 K 线图确认数据量和走势
@router.post("/preview")
def preview_ohlcv(req: RunRequest):
    from app.exchange.client import get_okx_ohlcv
    ohlcv = get_okx_ohlcv(req.symbol, req.timeframe, req.data_limit)
    return {
        "data": [{"t": int(r[0]), "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in ohlcv],
        "count": len(ohlcv),
    }


# 流式回测 — SSE 逐 K 线推送，前端实时渲染权益曲线和交易信号
@router.post("/run-stream")
def start_backtest_stream(req: RunRequest):
    return StreamingResponse(
        backtest_service.run_stream(
            strategy=req.strategy, symbol=req.symbol, timeframe=req.timeframe,
            initial_capital=req.initial_capital, position_ratio=req.position_ratio,
            fee_rate=req.fee_rate, warmup=req.warmup, data_limit=req.data_limit,
            temperature=req.temperature,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )


# 异步触发回测 — 立即返回 run_id，后台执行并通过 WebSocket 推送进度
@router.post("/run-async")
def start_backtest_async(req: RunRequest):
    return backtest_service.run_async(
        strategy=req.strategy, symbol=req.symbol, timeframe=req.timeframe,
        initial_capital=req.initial_capital, position_ratio=req.position_ratio,
        fee_rate=req.fee_rate, warmup=req.warmup, data_limit=req.data_limit,
        temperature=req.temperature,
    )


# 回测运行记录列表 — 按启动时间倒序，支持分页 ?page=1&page_size=20
@router.get("/runs")
def api_list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return backtest_service.list_runs(page=page, page_size=page_size)


# 单次回测完整详情 — 含配置参数、绩效指标、交易明细、权益曲线
@router.get("/runs/{run_id}")
def api_get_run(run_id: int):
    return backtest_service.get_run_detail(run_id)
