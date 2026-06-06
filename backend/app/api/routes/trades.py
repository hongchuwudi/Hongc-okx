"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: trades.py 交易记录API路由
描述: 交易记录 API — /api/trades 支持扁平数组和分页两种响应模式

包含:
- 函数: get_trades — 获取交易记录列表（支持 ?limit=N 扁平模式或 ?page=&page_size= 分页模式）
"""

from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from app.database import get_sync_session
from app.models.trading import Trade

router = APIRouter(prefix="/api")


@router.get("/trades")
def get_trades(
    limit: Optional[int] = Query(None, ge=1, le=500),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取交易记录列表，支持两种模式：
    - ?limit=N：返回扁平数组（前端默认使用）
    - ?page=&page_size=：返回分页对象
    """
    session: Session = get_sync_session()
    try:
        if limit is not None:
            # 扁平数组模式（兼容前端 fetchTrades(limit) 调用）
            trades = (
                session.query(Trade)
                .order_by(Trade.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": t.id,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else "",
                    "signal": t.signal,
                    "price": t.price,
                    "amount": t.amount,
                    "confidence": t.confidence,
                    "reason": t.reason,
                    "pnl": t.pnl,
                }
                for t in reversed(trades)
            ]

        # 分页模式
        total = session.query(Trade).count()
        offset = (page - 1) * page_size
        trades = (
            session.query(Trade)
            .order_by(Trade.timestamp.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        result = [
            {
                "id": t.id,
                "timestamp": t.timestamp.isoformat() if t.timestamp else "",
                "signal": t.signal,
                "price": t.price,
                "amount": t.amount,
                "confidence": t.confidence,
                "reason": t.reason,
                "pnl": t.pnl,
            }
            for t in reversed(trades)
        ]
        return {
            "data": result,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }
    finally:
        session.close()
