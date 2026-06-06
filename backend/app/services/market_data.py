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


class MarketDataService:
    """行情数据服务 — 封装交易所行情获取与 Redis 缓存逻辑"""

    def __init__(self, exchange: ExchangeClient):
        # 交易所客户端实例
        self._exchange = exchange

    async def get_current_price(self, symbol: str = "BTC/USDT:USDT") -> float:
        """获取当前价格，Redis 缓存 30 秒"""
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

    async def get_ohlcv(
        self,
        symbol: str = "BTC/USDT:USDT",
        timeframe: str = "1h",
        limit: int = 168,
    ) -> pd.DataFrame:
        """获取 K 线数据（含 Redis 缓存）"""
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

    async def get_account_info(self) -> dict:
        """获取账户信息（余额、权益）"""
        balance = await self._exchange.fetch_balance()
        usdt = balance.get("USDT", {})
        return {
            "balance": float(usdt.get("free", 0)),          # 可用余额
            "equity": float(balance.get("total", {}).get("USDT", 0)),  # 总权益
            "leverage": 1,                                  # 杠杆倍数
        }

    async def get_positions(self, symbol: str = "BTC/USDT:USDT") -> dict | None:
        """获取当前持仓，无持仓时返回 None"""
        positions = await self._exchange.fetch_positions([symbol])
        for pos in positions:
            if pos["symbol"] == symbol and float(pos.get("contracts", 0)) > 0:
                return {
                    "side": pos["side"],                    # 持仓方向 long/short
                    "size": float(pos["contracts"]),         # 持仓数量
                    "entry_price": float(pos.get("entryPrice", 0)),  # 开仓均价
                    "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),  # 未实现盈亏
                    "leverage": float(pos.get("leverage", 1)),  # 杠杆倍数
                }
        return None


def _symbol_short(symbol: str) -> str:
    """将交易对符号缩写为小写币种名（如 BTC/USDT:USDT → btc）"""
    return symbol.split("/")[0].lower()
