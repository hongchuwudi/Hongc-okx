"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_circuit_cleared.py 熔断解除
描述: 熔断自动解除时无异常
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_circuit_cleared_no_error(mock_engine, sample_account):
    sig = Signal(signal="BUY", confidence="MEDIUM")
    mock_engine.risk.record_tick_success = AsyncMock(return_value={"action":"cleared","success_count":5})
    with patch("app.engine.loop.tick_persist.persist_tick", AsyncMock()), \
         patch("app.engine.loop.tick_persist.cache_signal", AsyncMock()), \
         patch("app.engine.loop.tick_persist.publish_event", AsyncMock()), \
         patch("app.agents.status.save_tick_agent_logs", AsyncMock()):
        from app.engine.loop.tick_persist import tick_persist_and_notify
        await tick_persist_and_notify(mock_engine, datetime.now(), 100.0, sample_account, None, sig, None)
