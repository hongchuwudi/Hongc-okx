"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: dashboard_service.py 仪表盘服务
描述: 仪表盘业务逻辑 — 系统状态查询、健康检查、权益曲线、K线数据

包含:
- 类: DashboardService — 仪表盘查询服务（系统状态/权益曲线/K线/健康检查）
"""

import time
from typing import Optional

from app.config import config
from app.database import get_sync_session
from app.services.config.runtime import get_runtime
from app.entities.system import SystemStatus
from app.entities.trading import EquitySnapshot, Trade
from app.core.exceptions import ExternalServiceError


# 仪表盘查询服务 — 封装系统状态查询、权益曲线、K线数据和健康检查
class DashboardService:

    def __init__(self):
        self._cache: dict = {}
        self._cache_ttl = 2  # 缓存有效期 2 秒

    # 从内存缓存中获取数据（未过期则返回）
    def _get_cache(self, key: str) -> Optional[dict]:
        entry = self._cache.get(key)
        if entry and time.time() - entry["ts"] < self._cache_ttl:
            return entry["data"]
        return None

    # 将数据写入内存缓存（带时间戳）
    def _set_cache(self, key: str, data):
        self._cache[key] = {"data": data, "ts": time.time()}

    # 数据库连接健康检查
    def check_health(self) -> dict:
        try:
            session = get_sync_session()
            session.execute("SELECT 1")
            session.close()
            return {"ok": True, "db": "postgresql", "connected": True}
        except Exception as e:
            raise ExternalServiceError("数据库连接失败", detail={"db": "postgresql", "error": str(e)})

    # 获取系统完整状态：运行状态、账户信息、持仓、AI 信号、绩效统计
    def get_status(self) -> dict:
        cached = self._get_cache("status")
        if cached:
            return cached

        session = get_sync_session()
        try:
            row = session.query(SystemStatus).filter_by(id=1).first()
            if row is None:
                return {
                    "status": "stopped", "last_update": None,
                    "agent_mode": get_runtime("agent_mode"),
                    "account": {"balance": 0, "equity": 0, "leverage": 1},
                    "market": {"price": 0, "change": 0, "timeframe": "1h", "mode": "cross-oneway"},
                    "position": None,
                    "performance": {"total_pnl": 0, "win_rate": 0, "total_trades": 0},
                    "ai_signal": {"signal": "HOLD", "confidence": "N/A", "reason": "", "stop_loss": 0, "take_profit": 0, "timestamp": None},
                    "tp_sl_orders": {"stop_loss_order_id": None, "take_profit_order_id": None},
                }

            position = None
            if row.position_side:
                position = {
                    "side": row.position_side, "size": row.position_size,
                    "entry_price": row.position_entry_price, "unrealized_pnl": row.position_unrealized_pnl,
                    "mark_price": row.position_mark_price, "pnl_pct": row.position_pnl_pct,
                    "margin": row.position_margin, "notional": row.position_notional,
                    "liquidation_price": row.position_liquidation_price,
                }

            trade_count = session.query(Trade).count()
            total_pnl, win_count = 0.0, 0
            if trade_count > 0:
                trades_rows = (
                    session.query(Trade.pnl)
                    .order_by(Trade.timestamp.desc()).limit(500).all()
                )
                sample_count = len(trades_rows)
                for (pnl_val,) in trades_rows:
                    if pnl_val:
                        total_pnl += pnl_val
                        if pnl_val > 0:
                            win_count += 1
                win_rate = round(win_count / sample_count * 100, 1) if sample_count > 0 else 0.0
            else:
                win_rate = 0.0

            data = {
                "status": row.status,
                "last_update": row.last_update.isoformat() if row.last_update else None,
                "account": {"balance": row.balance, "equity": row.equity, "leverage": row.leverage},
                "agent_mode": get_runtime("agent_mode"),
                "market": {"price": row.btc_price, "change": row.btc_change, "timeframe": row.timeframe or "1h", "mode": row.mode or "cross-oneway"},
                "position": position,
                "performance": {"total_pnl": round(total_pnl, 2), "win_rate": win_rate, "total_trades": trade_count},
                "ai_signal": {
                    "signal": row.ai_signal, "confidence": row.ai_confidence,
                    "reason": row.ai_reason, "stop_loss": row.ai_stop_loss,
                    "take_profit": row.ai_take_profit,
                    "timestamp": row.ai_timestamp.isoformat() if row.ai_timestamp else None,
                },
                "tp_sl_orders": {
                    "stop_loss_order_id": row.tp_sl_stop_loss_order_id,
                    "take_profit_order_id": row.tp_sl_take_profit_order_id,
                },
            }
            self._set_cache("status", data)
            return data
        finally:
            session.close()

    # 获取历史权益曲线数据点
    def get_equity_curve(self, limit: int) -> list[dict]:
        cached = self._get_cache(f"equity_{limit}")
        if cached:
            return cached

        session = get_sync_session()
        try:
            snaps = (
                session.query(EquitySnapshot)
                .order_by(EquitySnapshot.timestamp.asc()).limit(limit).all()
            )
            result = [
                {"timestamp": s.timestamp.isoformat() if s.timestamp else "", "equity": s.equity}
                for s in snaps
            ]
            self._set_cache(f"equity_{limit}", result)
            return result
        finally:
            session.close()

    # 获取 K 线数据（OHLCV）
    def get_kline_data(self, symbol: str, timeframe: str, limit: int) -> list[dict]:
        from app.exchange.client import get_okx_ohlcv

        raw = get_okx_ohlcv(symbol, timeframe, limit)
        return [
            {"time": int(r[0]), "open": float(r[1]), "high": float(r[2]),
             "low": float(r[3]), "close": float(r[4]), "volume": float(r[5])}
            for r in raw
        ]


# 全局单例
dashboard_service = DashboardService()
