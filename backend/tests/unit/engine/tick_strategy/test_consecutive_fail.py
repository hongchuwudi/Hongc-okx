"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_consecutive_fail.py 连续失败
描述: 第 5 次连续失败时计数正确
"""
import pytest
from unittest.mock import AsyncMock
@pytest.mark.asyncio
async def test_consecutive_fail_count(mock_engine, sample_df, sample_account):
    mock_engine.coordinator.analyze = AsyncMock(side_effect=Exception("timeout"))
    mock_engine._agent_fail_count = 4
    from app.engine.loop.tick_strategy import tick_analyze_strategy
    await tick_analyze_strategy(mock_engine, sample_df, 100.0, sample_account, None)
    assert mock_engine._agent_fail_count == 5
