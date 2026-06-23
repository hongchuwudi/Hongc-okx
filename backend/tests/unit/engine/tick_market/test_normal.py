"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_normal.py 正常行情
描述: 正常获取 OHLCV/价格/账户/持仓
"""
import pytest
@pytest.mark.asyncio
async def test_fetch_returns_all_fields(mock_engine):
    from app.engine.loop.tick_market import tick_fetch_market
    df, price, account, position = await tick_fetch_market(mock_engine)
    assert len(df) == 60 and price == 100.0
    assert account["equity"] == 10000.0 and position is None
