"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: trades.py 交易记录API路由
描述: 交易记录 API — 支持扁平数组和分页两种响应模式

包含:
- 端点: GET /api/trades — 查询历史交易记录
  - ?limit=N：返回扁平数组（前端默认使用）
  - ?page=&page_size=：返回分页对象
"""

from typing import Optional, Union

from fastapi import APIRouter, Query

from app.services.trading.trade import TradeService
from app.schemas.responses.trading import TradeItem, TradePageResponse

router = APIRouter(prefix="/api/v1")


# 查询历史交易记录 — 按时间倒序，支持两种查询模式：
# - 扁平模式: ?limit=20 → 返回最多 500 条的数组（前端默认）
# - 分页模式: ?page=1&page_size=20 → 返回 {data, page, total, total_pages}
@router.get("/trades", response_model=Union[list[TradeItem], TradePageResponse])
def get_trades(
    limit: Optional[int] = Query(None, ge=1, le=500),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return TradeService.query_trades(limit=limit, page=page, page_size=page_size)
