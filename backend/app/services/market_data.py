"""行情数据服务 — OKX 数据获取 + Redis 缓存"""

import io
import json

import pandas as pd

from app.database import get_redis
from app.exchange.client import ExchangeClient

CACHE_TTL_PRICE = 30     # 价格缓存 30 秒
CACHE_TTL_OHLCV = 60     # K线缓存 60 秒


class MarketDataService:

    def __init__(self, exchange: ExchangeClient):
        self._exchange = exchange

    async def get_current_price(self, symbol: str = "BTC/USDT:USDT") -> float:
        """获取当前价格，Redis 缓存 30 秒"""
        redis = await get_redis()
        cache_key = f"market:{_symbol_short(symbol)}:price"
        cached = await redis.get(cache_key)
        if cached:
            return float(cached)

        ticker = await self._exchange.fetch_ticker(symbol)
        price = float(ticker["last"])
        await redis.setex(cache_key, CACHE_TTL_PRICE, str(price))
        return price

    async def get_ohlcv(
        self,
        symbol: str = "BTC/USDT:USDT",
        timeframe: str = "1h",
        limit: int = 168,
    ) -> pd.DataFrame:
        """获取 K 线数据"""
        redis = await get_redis()
        cache_key = f"market:{_symbol_short(symbol)}:ohlcv:{timeframe}:{limit}"
        cached = await redis.get(cache_key)
        if cached:
            return pd.read_json(io.StringIO(str(cached)))

        df = await self._exchange.fetch_ohlcv(symbol, timeframe, limit)
        await redis.setex(cache_key, CACHE_TTL_OHLCV, df.to_json())
        return df

    async def get_account_info(self) -> dict:
        """获取账户信息"""
        balance = await self._exchange.fetch_balance()
        usdt = balance.get("USDT", {})
        return {
            "balance": float(usdt.get("free", 0)),
            "equity": float(balance.get("total", {}).get("USDT", 0)),
            "leverage": 1,
        }

    async def get_positions(self, symbol: str = "BTC/USDT:USDT") -> dict | None:
        """获取当前持仓"""
        positions = await self._exchange.fetch_positions([symbol])
        for pos in positions:
            if pos["symbol"] == symbol and float(pos.get("contracts", 0)) > 0:
                return {
                    "side": pos["side"],
                    "size": float(pos["contracts"]),
                    "entry_price": float(pos.get("entryPrice", 0)),
                    "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),
                    "leverage": float(pos.get("leverage", 1)),
                }
        return None


def _symbol_short(symbol: str) -> str:
    """BTC/USDT:USDT → btc"""
    return symbol.split("/")[0].lower()
