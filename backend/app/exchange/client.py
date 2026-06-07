"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: client.py 交易所门面
描述: 交易所统一入口 — 组合 OKX 各模块（行情/账户/交易/模式），对外暴露统一接口

包含:
- 类: ExchangeClient — 交易所客户端门面
"""

import ccxt

from app.config import config
from app.exchange.okx.okx_market import OkxMarket
from app.exchange.okx.okx_account import OkxAccount
from app.exchange.okx.okx_trade import OkxTrade
from app.exchange.okx.okx_setup import OkxSetup


class ExchangeClient:
    """OKX 交易所统一门面。将 ccxt 实例分发给各子模块。"""

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

        # 子模块
        self.market = OkxMarket(self._exchange)
        self.account = OkxAccount(self._exchange)
        self.trade = OkxTrade(self._exchange)
        self.setup = OkxSetup(self._exchange)

    # ── 向后兼容的快捷方法 ────────────────────────────────────

    async def fetch_ohlcv(self, *args, **kwargs):
        return await self.market.fetch_ohlcv(*args, **kwargs)

    async def fetch_ticker(self, *args, **kwargs):
        return await self.market.fetch_ticker(*args, **kwargs)

    async def fetch_balance(self, *args, **kwargs):
        return await self.account.fetch_balance(*args, **kwargs)

    async def fetch_positions(self, *args, **kwargs):
        return await self.account.fetch_positions(*args, **kwargs)

    async def create_order(self, *args, **kwargs):
        return await self.trade.create_order(*args, **kwargs)

    async def create_algo_order(self, *args, **kwargs):
        return await self.trade.create_algo_order(*args, **kwargs)

    async def cancel_algo_orders(self, *args, **kwargs):
        return await self.trade.cancel_algo_orders(*args, **kwargs)

    async def fetch_open_algo_orders(self, *args, **kwargs):
        return await self.trade.fetch_open_algo_orders(*args, **kwargs)

    async def set_position_mode(self, *args, **kwargs):
        return await self.setup.set_position_mode(*args, **kwargs)

    async def set_leverage(self, *args, **kwargs):
        return await self.setup.set_leverage(*args, **kwargs)
