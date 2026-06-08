"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: 仪表盘 schema — /api/status, /api/equity, /api/kline
"""

from typing import Optional
from pydantic import BaseModel


class AccountInfo(BaseModel):
    balance: float = 0
    equity: float = 0
    leverage: int = 1


class MarketInfo(BaseModel):
    price: float = 0
    change: float = 0
    timeframe: str = "1h"
    mode: str = "cross-oneway"


class PositionInfo(BaseModel):
    side: str
    size: float
    entry_price: float
    unrealized_pnl: float


class PerformanceInfo(BaseModel):
    total_pnl: float = 0
    win_rate: float = 0
    total_trades: int = 0


class AiSignalInfo(BaseModel):
    signal: str = "HOLD"
    confidence: str = "N/A"
    reason: str = ""
    stop_loss: float = 0
    take_profit: float = 0
    timestamp: Optional[str] = None


class TpSlOrdersInfo(BaseModel):
    stop_loss_order_id: Optional[str] = None
    take_profit_order_id: Optional[str] = None


class StatusResponse(BaseModel):
    """GET /api/status 完整仪表盘状态"""
    status: str = "stopped"
    last_update: Optional[str] = None
    agent_mode: str = "5_agent"
    account: AccountInfo = AccountInfo()
    market: MarketInfo = MarketInfo()
    position: Optional[PositionInfo] = None
    performance: PerformanceInfo = PerformanceInfo()
    ai_signal: AiSignalInfo = AiSignalInfo()
    tp_sl_orders: TpSlOrdersInfo = TpSlOrdersInfo()


class EquityPoint(BaseModel):
    """GET /api/equity 数据点"""
    timestamp: str
    equity: float


class KlinePoint(BaseModel):
    """GET /api/kline 数据点"""
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
