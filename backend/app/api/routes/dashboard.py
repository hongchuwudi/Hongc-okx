"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: dashboard.py 仪表盘API路由
描述: 仪表盘 API — 提供系统状态、健康检查、权益曲线和 K 线数据接口

包含:
- 函数: health — 数据库连接健康检查
- 函数: get_status — 获取系统完整运行状态（含账户、持仓、AI 信号、风控等）
- 函数: get_equity — 获取历史权益曲线数据
- 函数: get_kline — 获取 K 线数据（OHLCV），供前端 ECharts 渲染
- 常量: _cache — 简易内存缓存
- 常量: _CACHE_TTL — 缓存有效期（秒）
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_sync_session
from app.entities.system import SystemStatus
from app.entities.trading import EquitySnapshot

router = APIRouter(prefix="/api")

# 简易内存缓存，避免高频请求重复查库
_cache: dict = {}
_CACHE_TTL = 2  # 缓存有效期 2 秒


def _cache_get(key: str) -> Optional[dict]:
    """从内存缓存中获取数据（未过期则返回）"""
    import time
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    """将数据写入内存缓存（带时间戳）"""
    import time
    _cache[key] = {"data": data, "ts": time.time()}


@router.get("/health")
def health():
    """数据库连接健康检查端点"""
    try:
        session = get_sync_session()
        session.execute("SELECT 1")
        session.close()
        return {"ok": True, "db": "postgresql", "connected": True}
    except Exception as e:
        return {"ok": False, "db": "postgresql", "connected": False, "error": str(e)}


@router.get("/status")
def get_status():
    """获取系统完整状态：运行状态、账户信息、持仓、AI 信号、止盈止损订单等"""
    cached = _cache_get("status")
    if cached:
        return cached

    from app.entities.trading import Trade
    session = get_sync_session()
    try:
        # 从 SystemStatus 单行表读取当前状态
        row = session.query(SystemStatus).filter_by(id=1).first()
        if row is None:
            return {
                "status": "stopped",
                "last_update": None,
                "account": {"balance": 0, "equity": 0, "leverage": 1},
                "btc": {"price": 0, "change": 0, "timeframe": "1h", "mode": "cross-oneway"},
                "position": None,
                "performance": {"total_pnl": 0, "win_rate": 0, "total_trades": 0},
                "ai_signal": {"signal": "HOLD", "confidence": "N/A", "reason": "", "stop_loss": 0, "take_profit": 0, "timestamp": None},
                "tp_sl_orders": {"stop_loss_order_id": None, "take_profit_order_id": None},
            }

        # 组装持仓信息（如果有持仓）
        position = None
        if row.position_side:
            position = {
                "side": row.position_side,
                "size": row.position_size,
                "entry_price": row.position_entry_price,
                "unrealized_pnl": row.position_unrealized_pnl,
            }

        # 从最近 500 条 Trade 计算 performance（避免全表扫描）
        trade_count = session.query(Trade).count()
        total_pnl = 0.0
        win_count = 0
        if trade_count > 0:
            trades_rows = (
                session.query(Trade.pnl)
                .order_by(Trade.timestamp.desc())
                .limit(500)
                .all()
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
            "btc": {"price": row.btc_price, "change": row.btc_change, "timeframe": row.timeframe or "1h", "mode": row.mode or "cross-oneway"},
            "position": position,
            "performance": {"total_pnl": round(total_pnl, 2), "win_rate": win_rate, "total_trades": trade_count},
            "ai_signal": {
                "signal": row.ai_signal,
                "confidence": row.ai_confidence,
                "reason": row.ai_reason,
                "stop_loss": row.ai_stop_loss,
                "take_profit": row.ai_take_profit,
                "timestamp": row.ai_timestamp.isoformat() if row.ai_timestamp else None,
            },
            "tp_sl_orders": {
                "stop_loss_order_id": row.tp_sl_stop_loss_order_id,
                "take_profit_order_id": row.tp_sl_take_profit_order_id,
            },
        }
        _cache_set("status", data)
        return data
    finally:
        session.close()


@router.get("/equity")
def get_equity(limit: int = Query(500, ge=1, le=2000)):
    """获取历史权益曲线数据点，用于前端绘制权益走势图"""
    cached = _cache_get(f"equity_{limit}")
    if cached:
        return cached

    session = get_sync_session()
    try:
        snaps = (
            session.query(EquitySnapshot)
            .order_by(EquitySnapshot.timestamp.asc())
            .limit(limit)
            .all()
        )
        result = [
            {"timestamp": s.timestamp.isoformat() if s.timestamp else "", "equity": s.equity}
            for s in snaps
        ]
        _cache_set(f"equity_{limit}", result)
        return result
    finally:
        session.close()


@router.get("/kline")
def get_kline(
    symbol: str = Query("BTC/USDT:USDT"),
    timeframe: str = Query("1h"),
    limit: int = Query(100, ge=1, le=500),
):
    """获取 K 线数据（OHLCV），供前端 ECharts 渲染蜡烛图"""
    import ccxt
    from app.config import config

    exchange = ccxt.okx({"hostname": "www.okx.cab", "enableRateLimit": True, "verify": False})
    if config.okx.proxy:
        exchange.https_proxy = config.okx.proxy
    raw = exchange.fetch_ohlcv(symbol, timeframe, None, limit)
    result = [
        {"time": int(r[0]), "open": float(r[1]), "high": float(r[2]),
         "low": float(r[3]), "close": float(r[4]), "volume": float(r[5])}
        for r in raw
    ]
    return result
