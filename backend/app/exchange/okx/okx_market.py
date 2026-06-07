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


class OkxMarket(BaseExchangeClient):
    """OKX 行情接口。"""

    def __init__(self, exchange):
        self._ex = exchange

    async def fetch_ohlcv(self, symbol: str = "BTC/USDT:USDT", timeframe: str = "1h", limit: int = 168) -> pd.DataFrame:
        """获取 K 线数据，返回 DataFrame。"""
        raw = await self._run(self._ex.fetch_ohlcv, symbol, timeframe, None, limit)
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    async def fetch_ticker(self, symbol: str = "BTC/USDT:USDT") -> dict:
        """获取当前行情 ticker。"""
        return await self._run(self._ex.fetch_ticker, symbol)
