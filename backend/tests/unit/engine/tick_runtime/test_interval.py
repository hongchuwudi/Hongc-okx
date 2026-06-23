"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_interval.py 间隔切换
描述: Tick 间隔热切换
"""
import pytest
from unittest.mock import AsyncMock, patch
@pytest.mark.asyncio
async def test_interval_updated(mock_engine):
    mock_engine.scheduler._interval = 360
    with patch("app.engine.runtime.runtime_interval.get_runtime_async", AsyncMock(return_value=60)):
        from app.engine.runtime.runtime_interval import _sync_interval
        await _sync_interval(mock_engine)
    assert mock_engine.scheduler._interval == 60

@pytest.mark.asyncio
async def test_interval_unchanged_noop(mock_engine):
    mock_engine.scheduler._interval = 120
    with patch("app.engine.runtime.runtime_interval.get_runtime_async", AsyncMock(return_value=120)):
        from app.engine.runtime.runtime_interval import _sync_interval
        await _sync_interval(mock_engine)
    assert mock_engine.scheduler._interval == 120
