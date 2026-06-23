"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_error_stopped.py 停止档
描述: 失败达停止阈值时熔断停引擎
"""
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_stopped_trips_circuit(mock_engine):
    mock_engine.risk.record_tick_failure = AsyncMock(return_value={"action":"stopped","fail_count":10})
    with patch("app.engine.loop.tick_persist.publish_event", AsyncMock()) as mp:
        from app.engine.loop.tick_persist import tick_handle_error
        await tick_handle_error(mock_engine, ConnectionError("network"))
    mock_engine.risk.trip_circuit_breaker.assert_called_once()
    e = mp.call_args.args[0]
    assert e["type"] == "circuit_breaker" and e["state"] == "stopped"
