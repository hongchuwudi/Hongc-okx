"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: 交易记录 schema — /api/trades
"""

from pydantic import BaseModel


class TradeItem(BaseModel):
    """单笔交易记录"""
    id: int
    timestamp: str
    signal: str
    price: float
    amount: float
    confidence: str
    reason: str
    pnl: float


class TradePageResponse(BaseModel):
    """分页交易记录"""
    data: list[TradeItem]
    page: int
    page_size: int
    total: int
    total_pages: int
