"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: client.py 交易所门面
描述: 交易所统一入口 — 组合 OKX 各模块（行情/账户/交易/模式），对外暴露统一接口

包含:
- 类: ExchangeClient — 交易所客户端门面
- 函数: get_okx_ohlcv — 同步拉 K 线，主代理不通自动切备用
"""

import ccxt

from app.core.config import config
from app.exchange.okx.okx_market import OkxMarket
from app.exchange.okx.okx_account import OkxAccount
from app.exchange.okx.okx_trade import OkxTrade
from app.exchange.okx.okx_setup import OkxSetup
from app.core.exceptions import ExternalServiceError
from app.core.logger import get_logger

logger = get_logger()


# 创建 ccxt 实例（同步用，不含认证）
def _new_okx(proxy_url: str | None) -> ccxt.Exchange:
    ex = ccxt.okx({"hostname": "www.okx.cab", "enableRateLimit": True, "verify": False})
    ex.options["fetchMarkets"] = ["swap"]
    if proxy_url:
        ex.https_proxy = proxy_url
    return ex


# 同步拉取 K 线数据 — 记住当前可用代理，主挂了切备用，定时探活主
# OKX API 单次最多 300 条，通过分页循环拉取满足任意 limit
_okx_proxy = config.okx.proxy  # 当前使用的代理
_okx_probe = 0
_OKX_PAGE_SIZE = 300  # OKX API 单次最大返回条数

def get_okx_ohlcv(symbol: str, timeframe: str, limit: int) -> list:
    global _okx_proxy, _okx_probe
    # 每 10 次探一次主代理是否恢复
    if _okx_proxy != config.okx.proxy:
        _okx_probe += 1
        if _okx_probe >= 10:
            _okx_probe = 0
            _okx_proxy = config.okx.proxy

    def _fetch(ex, lmt, since=None):
        kwargs = {"limit": min(lmt, _OKX_PAGE_SIZE)}
        if since is not None:
            kwargs["since"] = since
        return ex.fetch_ohlcv(symbol, timeframe, **kwargs)

    def _do_fetch(proxy_url):
        ex = _new_okx(proxy_url)
        all_candles = []
        remaining = limit
        since = None

        while remaining > 0:
            try:
                candles = _fetch(ex, remaining, since=since)
            except Exception:
                if len(all_candles) > 0:
                    break  # 已有部分数据，停止分页
                raise

            if not candles:
                break

            all_candles = candles + all_candles  # 旧数据放前面
            remaining = limit - len(all_candles)

            if len(candles) < _OKX_PAGE_SIZE:
                break  # 返回不足一页，说明已到历史尽头

            # 下一次请求：比当前最旧的 K 线再早 1ms
            since = int(candles[0][0]) - 1

        return all_candles

    try:
        return _do_fetch(_okx_proxy)
    except ccxt.RequestTimeout:
        # 请求超时不等于代理不通，直接重试一次
        logger.warning(f"代理 {_okx_proxy} 请求超时，重试")
        try:
            return _do_fetch(_okx_proxy)
        except Exception:
            backup = config.okx.proxy_backup
            if not backup or _okx_proxy == backup:
                raise ExternalServiceError("OKX 请求超时，重试和代理切换均失败")
            logger.warning(f"超时重试失败，切到备用代理: {backup}")
            _okx_proxy = backup
            _okx_probe = 0
            return _do_fetch(backup)
    except Exception:
        backup = config.okx.proxy_backup
        if not backup or _okx_proxy == backup:
            raise ExternalServiceError("OKX API 调用失败，代理切换不可用")
        logger.warning(f"代理 {_okx_proxy} 不通，切到备用: {backup}")
        _okx_proxy = backup
        _okx_probe = 0
        return _do_fetch(backup)


# OKX 交易所统一门面。将 ccxt 实例分发给各子模块。
class ExchangeClient:

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

        self._proxy = okx_cfg.proxy
        self._proxy_backup = okx_cfg.proxy_backup
        self._use_backup = False
        if self._proxy:
            self._exchange.https_proxy = self._proxy

        # 子模块
        self.market = OkxMarket(self._exchange)
        self.account = OkxAccount(self._exchange)
        self.trade = OkxTrade(self._exchange)
        self.setup = OkxSetup(self._exchange)

    # 切换到备用代理（主代理不通时调用，下次请求生效）
    def switch_to_backup(self) -> bool:
        if not self._proxy_backup:
            return False
        if self._use_backup:
            return False  # 已经在用备用，不再切换
        self._exchange.https_proxy = self._proxy_backup
        self._use_backup = True
        logger.warning(f"主代理不通，已切换到备用: {self._proxy_backup}")
        return True

    # 切回主代理（恢复后调用）
    def switch_to_primary(self) -> None:
        if self._proxy:
            self._exchange.https_proxy = self._proxy
            self._use_backup = False
            logger.info("已切回主代理")

    # 检查当前是否使用备用代理
    @property
    def use_backup(self) -> bool:
        return self._use_backup

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

    async def fetch_my_trades(self, *args, **kwargs):
        return await self.trade.fetch_my_trades(*args, **kwargs)

    async def set_position_mode(self, *args, **kwargs):
        return await self.setup.set_position_mode(*args, **kwargs)

    async def set_leverage(self, *args, **kwargs):
        return await self.setup.set_leverage(*args, **kwargs)
