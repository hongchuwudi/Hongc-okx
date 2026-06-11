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

from app.database import get_redis
from app.exchange.client import ExchangeClient

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
        price = float(ticker["last"])
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
        usdt = balance.get("USDT", {})
        return {
            "balance": float(usdt.get("free", 0)),          # 可用余额
            "equity": float(balance.get("total", {}).get("USDT", 0)),  # 总权益
            "leverage": 1,                                  # 杠杆倍数
        }

    # 获取当前持仓，无持仓时返回 None
    async def get_positions(self, symbol: str) -> dict | None:
        positions = await self._exchange.fetch_positions([symbol])
        for pos in positions:
            if pos["symbol"] == symbol and float(pos.get("contracts", 0)) > 0:
                # ccxt OKX 返回的持仓信息字段
                sz = float(pos.get("contracts", 0))
                entry = float(pos.get("entryPrice", 0))
                mark = float(pos.get("markPrice", 0))
                notional = float(pos.get("notional", 0))  # OKX 可能不直接返回
                margin = float(pos.get("initialMargin", 0))
                liq = float(pos.get("liquidationPrice", 0))
                pnl = float(pos.get("unrealizedPnl", 0))
                pnl_pct = float(pos.get("percentage", 0)) * 100 if pos.get("percentage") else 0
                lev = float(pos.get("leverage", 1))
                # 如果 notional 为 0，用 size * entry / leverage 估算
                if notional <= 0:
                    notional = sz * entry * 0.01  # DOGE 合约 0.01 为 1 张
                return {
                    "side": pos["side"],
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
