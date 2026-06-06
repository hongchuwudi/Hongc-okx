"""交易记录 API — /api/trades (支持分页和扁平数组两种模式)"""

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
    session: Session = get_sync_session()
    try:
        if limit is not None:
            # 扁平数组模式（兼容前端 fetchTrades(limit)）
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
