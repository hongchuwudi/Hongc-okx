"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: okx_trade.py OKX交易
描述: OKX 交易接口 — 下单、算法止盈止损、撤销算法单

包含:
- 类: OkxTrade — OKX 交易执行
"""

from typing import List

from app.exchange.base import BaseExchangeClient


class OkxTrade(BaseExchangeClient):
    """OKX 交易接口。"""

    def __init__(self, exchange):
        self._ex = exchange

    async def create_order(self, symbol: str, order_type: str, side: str,
                           amount: float, price: float | None = None) -> dict:
        """创建市价/限价订单。"""
        return await self._run(self._ex.create_order, symbol, order_type, side, amount, price)

    async def create_algo_order(self, symbol: str, side: str, order_type: str,
                                amount: float, trigger_price: float,
                                algo_price: float | None = None) -> dict:
        """创建算法订单（止盈/止损）。"""
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {
            "instId": okx_symbol, "side": side, "sz": str(amount),
            "ordType": order_type, "triggerPx": str(trigger_price), "tdMode": "cross",
        }
        if algo_price:
            params["orderPx"] = str(algo_price)
        return await self._run(lambda: self._ex.private_post_trade_order_algo(params))

    async def cancel_algo_orders(self, symbol: str) -> dict:
        """撤销指定交易对的所有算法订单。"""
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        return await self._run(lambda: self._ex.private_post_trade_cancel_algos({"instId": okx_symbol}))

    async def fetch_open_algo_orders(self, symbol: str) -> List[dict]:
        """查询活跃算法订单列表。"""
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        result = await self._run(lambda: self._ex.private_get_trade_orders_algo_pending({"instId": okx_symbol}))
        return result.get("data", [])
