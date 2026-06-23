"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_timeout_retry.py 超时重试
描述: 首次 RequestTimeout 后重试成功
"""
import pytest
@pytest.mark.asyncio
async def test_timeout_retry_succeeds(mock_engine, sample_df):
    call_count = [0]
    async def flaky(*a, **kw):
        call_count[0] += 1
        if call_count[0] == 1:
            import ccxt; raise ccxt.RequestTimeout("timeout")
        return sample_df
    mock_engine.market_data.get_ohlcv = flaky
    from app.engine.loop.tick_market import tick_fetch_market
    await tick_fetch_market(mock_engine)
    assert call_count[0] == 2
