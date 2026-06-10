"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: okx_market.py OKX行情
描述: OKX 行情接口 — K线、Ticker

包含:
- 类: OkxMarket — OKX 行情数据获取
"""

import pandas as pd

from app.exchange.base import BaseExchangeClient


# OKX 行情接口。
class OkxMarket(BaseExchangeClient):

    def __init__(self, exchange):
        self._ex = exchange

    # 获取 K 线数据，返回 DataFrame。
    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 168) -> pd.DataFrame:
        raw = await self._run(self._ex.fetch_ohlcv, symbol, timeframe, None, limit)
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    # 获取当前行情 ticker。
    async def fetch_ticker(self, symbol: str) -> dict:
        return await self._run(self._ex.fetch_ticker, symbol)
