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


# OKX 交易接口。
class OkxTrade(BaseExchangeClient):

    def __init__(self, exchange):
        self._ex = exchange

    # 创建市价/限价订单。
    async def create_order(self, symbol: str, order_type: str, side: str,
                           amount: float, price: float | None = None) -> dict:
        return await self._run(self._ex.create_order, symbol, order_type, side, amount, price)

    # 创建算法订单（止损或止盈）。
    async def create_algo_order(self, symbol: str, side: str, order_type: str,
                                amount: float, trigger_price: float,
                                algo_price: float | None = None,
                                sl_side: bool = True) -> dict:
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {
            "instId": okx_symbol, "side": side, "sz": self._ex.amount_to_precision(symbol, amount),
            "ordType": order_type, "tdMode": "cross",
        }
        if sl_side:
            params["slTriggerPx"] = str(trigger_price)
            params["slOrdPx"] = str(algo_price) if algo_price else "-1"
        else:
            params["tpTriggerPx"] = str(trigger_price)
            params["tpOrdPx"] = str(algo_price) if algo_price else "-1"
        return await self._run(lambda: self._ex.private_post_trade_order_algo(params))

    # 挂止损止盈单（不再推荐使用，conditional 不支持同时 SL+TP）
    async def set_stop_loss_take_profit(self, symbol: str, close_side: str,
                                         amount: float, sl: float, tp: float) -> dict:
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        params = {
            "instId": okx_symbol, "tdMode": "cross",
            "side": close_side, "sz": self._ex.amount_to_precision(symbol, amount),
            "ordType": "conditional",
            "slTriggerPx": str(sl), "slOrdPx": "-1",
            "tpTriggerPx": str(tp), "tpOrdPx": "-1",
        }
        return await self._run(lambda: self._ex.private_post_trade_order_algo(params))

    # 撤销指定交易对的所有算法订单。
    async def cancel_algo_orders(self, symbol: str) -> dict:
        # 先查活跃算法单，逐个撤销（避免 instId 参数兼容性问题）
        orders = await self.fetch_open_algo_orders(symbol)
        for o in orders:
            aid = o.get("algoId", "")
            if aid:
                try:
                    await self._run(lambda aid=aid: self._ex.private_post_trade_cancel_algos({"algoId": aid}))
                except Exception:
                    pass
        return {"cancelled": len(orders)}

    # 查询活跃算法订单列表。
    async def fetch_open_algo_orders(self, symbol: str, ord_type: str = "conditional") -> List[dict]:
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        result = await self._run(lambda: self._ex.private_get_trade_orders_algo_pending(
            {"instId": okx_symbol, "ordType": ord_type}
        ))
        return result.get("data", [])
