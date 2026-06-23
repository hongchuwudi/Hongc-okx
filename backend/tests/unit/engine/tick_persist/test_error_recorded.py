"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_error_recorded.py 错误记录
描述: 异常时调用 record_tick_failure
"""
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_records_failure(mock_engine):
    mock_engine.risk.record_tick_failure = AsyncMock(return_value={})
    with patch("app.engine.loop.tick_persist.publish_event", AsyncMock()):
        from app.engine.loop.tick_persist import tick_handle_error
        await tick_handle_error(mock_engine, ValueError("test"))
    mock_engine.risk.record_tick_failure.assert_called_once_with("ValueError")
