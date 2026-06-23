"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_network_switch.py 切换代理
描述: NetworkError 时调用 switch_to_backup
"""
import pytest
@pytest.mark.asyncio
async def test_network_error_switches_proxy(mock_engine, sample_df):
    call_count = [0]
    async def flaky(*a, **kw):
        call_count[0] += 1
        if call_count[0] == 1:
            import ccxt; raise ccxt.NetworkError("connect failed")
        return sample_df
    mock_engine.market_data.get_ohlcv = flaky
    from app.engine.loop.tick_market import tick_fetch_market
    await tick_fetch_market(mock_engine)
    mock_engine.exchange.switch_to_backup.assert_called_once()
