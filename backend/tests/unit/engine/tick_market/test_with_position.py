"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_with_position.py 有持仓
描述: 有持仓时正常返回持仓信息
"""
import pytest
from unittest.mock import AsyncMock
@pytest.mark.asyncio
async def test_fetch_with_position(mock_engine, sample_position):
    mock_engine.market_data.get_positions = AsyncMock(return_value=sample_position)
    from app.engine.loop.tick_market import tick_fetch_market
    df, price, account, position = await tick_fetch_market(mock_engine)
    assert position is not None and position["side"] == "long"
