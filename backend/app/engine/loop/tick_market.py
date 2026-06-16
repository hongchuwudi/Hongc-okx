"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_market.py 行情获取
描述: 每个 tick 从 OKX 获取 K 线、价格、账户、持仓数据（含代理切换 + 重试）

包含:
- 函数: tick_fetch_market — 获取全部行情数据
"""

import pandas as pd
import ccxt

from app.core.exceptions import ExternalServiceError
from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

logger = get_logger()


async def tick_fetch_market(engine) -> tuple[pd.DataFrame, float, dict, dict | None]:
    """获取 OKX 行情数据（K 线 / 价格 / 账户 / 持仓）。

    含主备代理切换逻辑和 2 次重试。
    返回: (df, price, account, position)
    """
    timeframe = await get_runtime_async("timeframe")
    data_points = int(await get_runtime_async("data_points"))

    # 如果当前用备用代理，每次 tick 都尝试切回主代理
    if engine.exchange.use_backup:
        engine.exchange.switch_to_primary()
        logger.info("尝试切回主代理...")

    for attempt in range(2):
        try:
            df = await engine.market_data.get_ohlcv(engine._symbol, timeframe, data_points)
            price = await engine.market_data.get_current_price(engine._symbol)
            account = await engine.market_data.get_account_info()
            position = await engine.market_data.get_positions(engine._symbol)
            engine._probe_count = 0
            break
        except ccxt.RequestTimeout as timeout_err:
            if attempt == 0:
                logger.warning(f"请求超时，重试: {timeout_err}")
                continue
            raise ExternalServiceError(f"OKX 请求超时，重试失败: {timeout_err}") from timeout_err
        except (ccxt.NetworkError, ccxt.ExchangeNotAvailable) as net_err:
            if attempt == 0 and engine.exchange.switch_to_backup():
                logger.warning(f"网络错误，切换代理重试: {net_err}")
                continue
            raise ExternalServiceError(f"OKX 网络不可达，代理切换失败: {net_err}") from net_err
        except (TypeError, ValueError, KeyError) as data_err:
            import traceback
            tb_str = traceback.format_exc()
            func_hint = ""
            if "get_current_price" in tb_str:
                func_hint = " [来源: get_current_price]"
            elif "get_positions" in tb_str:
                func_hint = " [来源: get_positions]"
            elif "get_account_info" in tb_str:
                func_hint = " [来源: get_account_info]"
            elif "get_ohlcv" in tb_str:
                func_hint = " [来源: get_ohlcv]"
            logger.error(f"行情数据解析异常(非网络错误): {data_err}{func_hint}")
            raise ExternalServiceError(f"OKX 返回数据异常{func_hint}: {data_err}") from data_err

    return df, price, account, position
