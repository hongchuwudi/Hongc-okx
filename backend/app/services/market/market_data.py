"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: market_data.py 中文名
描述: 行情数据服务 — 从 OKX 交易所获取行情数据并通过 Redis 缓存

包含:
- 类: MarketDataService — 行情数据服务，封装交易所行情获取与缓存逻辑
- 函数: _symbol_short — 将交易对符号缩写为小写币种名
- 常量: CACHE_TTL_PRICE — 价格缓存过期时间（秒）
- 常量: CACHE_TTL_OHLCV — K线数据缓存过期时间（秒）
"""

import io
import json

import pandas as pd

from app.core.database import get_redis
from app.exchange.client import ExchangeClient
from app.core.exceptions import ExternalServiceError
from app.core.logger import get_logger

logger = get_logger()

# 价格缓存过期时间：30秒
CACHE_TTL_PRICE = 30
# K线数据缓存过期时间：60秒
CACHE_TTL_OHLCV = 60


# 行情数据服务 — 封装交易所行情获取与 Redis 缓存逻辑
class MarketDataService:

    def __init__(self, exchange: ExchangeClient):
        # 交易所客户端实例
        self._exchange = exchange

    # 获取当前价格，Redis 缓存 30 秒
    async def get_current_price(self, symbol: str) -> float:
        redis = await get_redis()
        cache_key = f"market:{_symbol_short(symbol)}:price"
        # 尝试从缓存读取
        cached = await redis.get(cache_key)
        if cached:
            return float(cached)

        # 缓存未命中，从交易所获取
        ticker = await self._exchange.fetch_ticker(symbol)
        last_price = _safe_float(ticker.get("last"), None)
        if last_price is None:
            last_price = _safe_float(ticker.get("close") or ticker.get("bid"), 0)
            if last_price == 0:
                raise ExternalServiceError("OKX ticker 未返回价格", detail={"symbol": symbol})
        price = float(last_price)
        # 写入缓存
        await redis.setex(cache_key, CACHE_TTL_PRICE, str(price))
        return price

    # 获取 K 线数据（含 Redis 缓存）
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 168,
    ) -> pd.DataFrame:
        redis = await get_redis()
        cache_key = f"market:{_symbol_short(symbol)}:ohlcv:{timeframe}:{limit}"
        # 尝试从缓存读取
        cached = await redis.get(cache_key)
        if cached:
            return pd.read_json(io.StringIO(str(cached)))

        # 缓存未命中，从交易所获取
        df = await self._exchange.fetch_ohlcv(symbol, timeframe, limit)
        # 写入缓存
        await redis.setex(cache_key, CACHE_TTL_OHLCV, df.to_json())
        return df

    # 获取账户信息（余额、权益）
    async def get_account_info(self) -> dict:
        balance = await self._exchange.fetch_balance()
        usdt = balance.get("USDT", {}) or {}
        total_balance = balance.get("total", {}) or {}
        usdt_total = total_balance.get("USDT", 0)
        return {
            "balance": _safe_float(usdt.get("free"), 0),
            "equity": _safe_float(usdt_total, 0),
            "leverage": 1,
        }

    # 获取当前持仓，无持仓时返回 None
    async def get_positions(self, symbol: str) -> dict | None:
        positions = await self._exchange.fetch_positions([symbol])
        for pos in positions:
            # dict.get(key, default) 在 key 存在但值为 None 时返回 None 而非 default
            # OKX 模拟盘可能返回 contracts=null，必须用 `or 0` 兜底
            contracts = _safe_float(pos.get("contracts"), 0)
            if pos["symbol"] == symbol and contracts > 0:
                # ccxt OKX 返回的持仓信息字段
                sz = contracts
                raw_entry = pos.get("entryPrice")
                mark = _safe_float(pos.get("markPrice"), 0)
                # OKX 模拟盘可能返回 avgPx="0"，ccxt 解析为 entryPrice=0.0
                # 此时用 markPrice 兜底，避免入场价为 0 导致盈亏计算失真
                if raw_entry is not None and _safe_float(raw_entry, 0) > 0:
                    entry = _safe_float(raw_entry, 0)
                else:
                    entry = mark if mark > 0 else 0.0
                    if entry == 0.0:
                        logger.warning(f"OKX entryPrice 和 markPrice 均为 0，持仓数据可能异常")
                    elif raw_entry is not None and _safe_float(raw_entry, 0) == 0:
                        logger.warning(f"OKX entryPrice=0，用 markPrice={mark} 兜底")
                notional = _safe_float(pos.get("notional"), 0)  # OKX 可能不直接返回
                margin = _safe_float(pos.get("initialMargin"), 0)
                liq = _safe_float(pos.get("liquidationPrice"), 0)
                pnl = _safe_float(pos.get("unrealizedPnl"), 0)
                # ccxt percentage 字段已是百分数（如 1.6455 表示 1.6455%），
                # 不再 ×100（旧逻辑会算成 164.55%，污染盈亏显示）
                pnl_pct = _safe_float(pos.get("percentage"), 0) if pos.get("percentage") else 0
                lev = _safe_float(pos.get("leverage"), 1)
                # 如果 notional 为 0，用 size * entry / leverage 估算
                if notional <= 0:
                    notional = sz * entry * 0.01  # DOGE 合约 0.01 为 1 张
                # side 规范化 — ccxt 可能返回 None/空字符串，统一为 long/short/None
                raw_side = pos.get("side")
                side = raw_side if raw_side in ("long", "short") else None
                if side is None:
                    logger.warning(f"OKX 持仓 side 异常: {raw_side!r}，持仓数据可能不可用")
                return {
                    "side": side,
                    "size": sz,
                    "entry_price": entry,
                    "mark_price": mark,
                    "unrealized_pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "leverage": lev,
                    "margin": margin,
                    "notional": notional,
                    "liquidation_price": liq,
                }
        return None


# 将交易对符号缩写为小写币种名（如 BTC/USDT:USDT → btc）
def _symbol_short(symbol: str) -> str:
    return symbol.split("/")[0].lower()


# 安全转 float —— 当值为 None 时返回默认值，避免 float(None) → TypeError
def _safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
