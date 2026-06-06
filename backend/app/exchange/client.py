"""OKX 交易所封装 — ccxt 的异步包装"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import ccxt
import pandas as pd

from app.config import config

_executor = ThreadPoolExecutor(max_workers=4)


class ExchangeClient:
    """OKX 交易所客户端（同步 ccxt → 异步接口）"""

    def __init__(self):
        okx_cfg = config.okx
        self._exchange = ccxt.okx({
            "apiKey": okx_cfg.api_key,
            "secret": okx_cfg.secret,
            "password": okx_cfg.password,
            "hostname": "www.okx.cab",
            "enableRateLimit": True,
            "verify": False,
            "options": {"defaultType": "swap"},
        })
        if okx_cfg.sandbox:
            self._exchange.set_sandbox_mode(True)
        if okx_cfg.proxy:
            self._exchange.https_proxy = okx_cfg.proxy

    # ── 行情 ────────────────────────────────────────────────

    async def fetch_ohlcv(
        self, symbol: str = "BTC/USDT:USDT", timeframe: str = "1h", limit: int = 168
    ) -> pd.DataFrame:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            _executor, self._exchange.fetch_ohlcv, symbol, timeframe, None, limit
        )
        df = pd.DataFrame(
            raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    async def fetch_ticker(self, symbol: str = "BTC/USDT:USDT") -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._exchange.fetch_ticker, symbol
        )

    # ── 账户 ────────────────────────────────────────────────

    async def fetch_balance(self) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._exchange.fetch_balance
        )

    async def fetch_positions(
        self, symbols: List[str] | None = None
    ) -> List[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._exchange.fetch_positions, symbols
        )

    # ── 交易 ────────────────────────────────────────────────

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
    ) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self._exchange.create_order,
            symbol, order_type, side, amount, price,
        )

    async def create_algo_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        trigger_price: float,
        algo_price: float | None = None,
    ) -> dict:
        """创建算法订单（止盈/止损）"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {
            "instId": okx_symbol,
            "side": side,
            "sz": str(amount),
            "ordType": order_type,
            "triggerPx": str(trigger_price),
            "tdMode": "cross",
        }
        if algo_price:
            params["orderPx"] = str(algo_price)
        return await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_trade_order_algo(params),
        )

    async def cancel_algo_orders(self, symbol: str) -> dict:
        """撤销所有算法订单"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {"instId": okx_symbol}
        return await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_trade_cancel_algos(params),
        )

    async def fetch_open_algo_orders(self, symbol: str) -> List[dict]:
        """查询活跃的算法订单"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {"instId": okx_symbol}
        result = await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_get_trade_orders_algo_pending(params),
        )
        return result.get("data", [])

    # ── 模式管理 ────────────────────────────────────────────

    async def set_position_mode(self, hedged: bool = False) -> None:
        """设置持仓模式（单向/双向）"""
        loop = asyncio.get_event_loop()
        pos_mode = "long_short_mode" if hedged else "net_mode"
        await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_account_set_position_mode(
                {"posMode": pos_mode}
            ),
        )

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        """设置杠杆倍数"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_account_set_leverage(
                {"instId": okx_symbol, "lever": str(leverage), "mgnMode": "cross"}
            ),
        )
