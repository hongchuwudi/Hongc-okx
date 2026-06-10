"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: okx_setup.py OKX模式管理
描述: OKX 模式管理 — 持仓模式、杠杆设置

包含:
- 类: OkxSetup — OKX 模式/杠杆配置
"""

from app.exchange.base import BaseExchangeClient


# OKX 模式管理接口。
class OkxSetup(BaseExchangeClient):

    def __init__(self, exchange):
        self._ex = exchange

    # 设置持仓模式：单向(net_mode) 或 双向(long_short_mode)。
    async def set_position_mode(self, hedged: bool = False):
        pos_mode = "long_short_mode" if hedged else "net_mode"
        await self._run(lambda: self._ex.private_post_account_set_position_mode({"posMode": pos_mode}))

    # 设置杠杆倍数（全仓模式）。
    async def set_leverage(self, symbol: str, leverage: int):
        okx_symbol = symbol.replace("/", "-").replace(":USDT", "-SWAP")
        await self._run(lambda: self._ex.private_post_account_set_leverage(
            {"instId": okx_symbol, "lever": str(leverage), "mgnMode": "cross"}))
