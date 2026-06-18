"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: test_tick_market.py 行情获取测试
描述: 验证行情获取正常返回 + OKX 异常重试降级

包含:
- TestMarketNormal — 正常获取行情
- TestMarketRetry — 超时重试逻辑
"""

import pytest
from unittest.mock import AsyncMock


class TestMarketNormal:
    """正常行情获取返回完整数据。"""

    @pytest.mark.asyncio
    async def test_fetch_returns_all_fields(self, mock_engine):
        from app.engine.loop.tick_market import tick_fetch_market
        df, price, account, position = await tick_fetch_market(mock_engine)
        assert len(df) == 60
        assert price == 100.0
        assert account["equity"] == 10000.0
        assert position is None

    @pytest.mark.asyncio
    async def test_fetch_with_position(self, mock_engine, sample_position):
        mock_engine.market_data.get_positions = AsyncMock(return_value=sample_position)
        from app.engine.loop.tick_market import tick_fetch_market
        df, price, account, position = await tick_fetch_market(mock_engine)
        assert position is not None
        assert position["side"] == "long"


class TestMarketRetry:
    """网络异常时的重试和代理切换。"""

    @pytest.mark.asyncio
    async def test_timeout_retry_succeeds(self, mock_engine, sample_df):
        """第一次超时第二次成功。"""
        call_count = [0]

        async def flaky_fetch(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                import ccxt
                raise ccxt.RequestTimeout("timeout")
            return sample_df

        mock_engine.market_data.get_ohlcv = flaky_fetch
        from app.engine.loop.tick_market import tick_fetch_market
        df, price, account, position = await tick_fetch_market(mock_engine)
        assert call_count[0] == 2  # 重试了一次

    @pytest.mark.asyncio
    async def test_network_error_switches_proxy(self, mock_engine, sample_df):
        """网络错误时切换备用代理。"""
        call_count = [0]

        async def flaky_fetch(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                import ccxt
                raise ccxt.NetworkError("connect failed")
            return sample_df

        mock_engine.market_data.get_ohlcv = flaky_fetch
        from app.engine.loop.tick_market import tick_fetch_market
        await tick_fetch_market(mock_engine)
        mock_engine.exchange.switch_to_backup.assert_called_once()
