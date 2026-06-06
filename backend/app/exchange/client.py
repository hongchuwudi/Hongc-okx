"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: client.py 中文名
描述: OKX 交易所封装 — 基于 ccxt 的异步包装，提供行情、账户、交易、模式管理接口

包含:
- 常量: _executor — 全局线程池执行器
- 类: ExchangeClient — OKX 交易所客户端，同步 ccxt 转异步接口
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import ccxt
import pandas as pd

from app.config import config

# 全局线程池执行器（最大 4 个工作线程）
_executor = ThreadPoolExecutor(max_workers=4)


class ExchangeClient:
    """OKX 交易所客户端（同步 ccxt 封装为异步接口）"""

    def __init__(self):
        okx_cfg = config.okx
        # 初始化 ccxt OKX 交易所实例
        self._exchange = ccxt.okx({
            "apiKey": okx_cfg.api_key,
            "secret": okx_cfg.secret,
            "password": okx_cfg.password,
            "hostname": "www.okx.cab",
            "enableRateLimit": True,
            "verify": False,
            "options": {"defaultType": "swap"},   # 默认为永续合约
        })
        if okx_cfg.sandbox:
            self._exchange.set_sandbox_mode(True)  # 启用模拟盘
        if okx_cfg.proxy:
            self._exchange.https_proxy = okx_cfg.proxy  # 设置代理

    # ── 行情接口 ─────────────────────────────────────────────

    async def fetch_ohlcv(
        self, symbol: str = "BTC/USDT:USDT", timeframe: str = "1h", limit: int = 168
    ) -> pd.DataFrame:
        """获取 K 线数据，返回 DataFrame"""
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
        """获取当前行情 ticker"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._exchange.fetch_ticker, symbol
        )

    # ── 账户接口 ─────────────────────────────────────────────

    async def fetch_balance(self) -> dict:
        """获取账户余额"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._exchange.fetch_balance
        )

    async def fetch_positions(
        self, symbols: List[str] | None = None
    ) -> List[dict]:
        """获取持仓列表"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, self._exchange.fetch_positions, symbols
        )

    # ── 交易接口 ─────────────────────────────────────────────

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: float | None = None,
    ) -> dict:
        """创建市价/限价订单"""
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
        """创建算法订单（止盈/止损），价格触发后市价或限价平仓"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {
            "instId": okx_symbol,
            "side": side,
            "sz": str(amount),
            "ordType": order_type,
            "triggerPx": str(trigger_price),
            "tdMode": "cross",                  # 全仓保证金模式
        }
        if algo_price:
            params["orderPx"] = str(algo_price)  # 限价执行价格
        return await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_trade_order_algo(params),
        )

    async def cancel_algo_orders(self, symbol: str) -> dict:
        """撤销指定交易对的所有算法订单"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {"instId": okx_symbol}
        return await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_trade_cancel_algos(params),
        )

    async def fetch_open_algo_orders(self, symbol: str) -> List[dict]:
        """查询指定交易对当前活跃的算法订单列表"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {"instId": okx_symbol}
        result = await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_get_trade_orders_algo_pending(params),
        )
        return result.get("data", [])

    # ── 模式管理接口 ─────────────────────────────────────────

    async def set_position_mode(self, hedged: bool = False) -> None:
        """设置持仓模式：单向模式（net_mode）或双向模式（long_short_mode）"""
        loop = asyncio.get_event_loop()
        pos_mode = "long_short_mode" if hedged else "net_mode"
        await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_account_set_position_mode(
                {"posMode": pos_mode}
            ),
        )

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        """设置交易对的杠杆倍数（全仓模式）"""
        loop = asyncio.get_event_loop()
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        await loop.run_in_executor(
            _executor,
            lambda: self._exchange.private_post_account_set_leverage(
                {"instId": okx_symbol, "lever": str(leverage), "mgnMode": "cross"}
            ),
        )
