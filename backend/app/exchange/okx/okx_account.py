"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: okx_account.py OKX账户
描述: OKX 账户接口 — 余额、持仓

包含:
- 类: OkxAccount — OKX 账户/持仓查询
"""

from typing import List

from app.exchange.base import BaseExchangeClient


# OKX 账户接口。
class OkxAccount(BaseExchangeClient):

    def __init__(self, exchange):
        self._ex = exchange

    # 获取账户余额。
    async def fetch_balance(self) -> dict:
        return await self._run(self._ex.fetch_balance)

    # 获取持仓列表。
    async def fetch_positions(self, symbols: List[str] | None = None) -> List[dict]:
        return await self._run(self._ex.fetch_positions, symbols)
