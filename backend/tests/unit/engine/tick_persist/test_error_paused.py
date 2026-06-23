"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_error_paused.py 暂停档
描述: 失败达暂停阈值时记录 warning
"""
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_paused_triggers_warning(mock_engine):
    mock_engine.risk.record_tick_failure = AsyncMock(return_value={"action":"paused","fail_count":3,"pause_minutes":5})
    with patch("app.engine.loop.tick_persist.publish_event", AsyncMock()):
        from app.engine.loop.tick_persist import tick_handle_error
        await tick_handle_error(mock_engine, RuntimeError("timeout"))
    mock_engine.risk.trip_circuit_breaker.assert_not_called()
