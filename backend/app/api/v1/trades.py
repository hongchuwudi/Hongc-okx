"""
创建时间: 2026-06-06
作者: hongchuwudi
描述: 交易记录 API — 路由 + 参数 + 文档，业务逻辑全部下沉 service

包含:
- GET /api/v1/trades         — 系统数据库交易记录
- GET /api/v1/trades/okx     — OKX 真实成交记录
"""

from typing import Optional, Union

from fastapi import APIRouter, Query

from app.services.trading.trade import TradeService
from app.schemas.responses.trading import TradeItem, TradePageResponse

router = APIRouter(prefix="/api/v1")


# ── 系统数据库交易记录 ──────────────────────────────────

@router.get("/trades", response_model=Union[list[TradeItem], TradePageResponse])
def get_trades(
    limit: Optional[int] = Query(None, ge=1, le=500, description="返回条数，传此参数返回扁平数组"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """查询系统数据库中的历史交易记录，支持扁平/分页两种模式。"""
    return TradeService.query_trades(limit=limit, page=page, page_size=page_size)


# ── OKX 真实成交记录 ───────────────────────────────────

@router.get("/trades/okx")
async def get_okx_trades(
    symbol: str = Query("DOGE/USDT:USDT", description="交易对"),
    limit: int = Query(100, ge=1, le=100, description="从 OKX 拉取的原始条数上限"),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    side: Optional[str] = Query(None, description="筛选方向: buy | sell"),
    start_time: Optional[str] = Query(None, description="起始时间 ISO，如 2026-06-01T00:00:00"),
    end_time: Optional[str] = Query(None, description="结束时间 ISO"),
):
    """从 OKX 拉取个人真实成交记录，支持分页、方向筛选、时间范围。"""
    return await TradeService.query_okx_trades(
        symbol=symbol, limit=limit, page=page, page_size=page_size,
        side=side, start_time=start_time, end_time=end_time,
    )
