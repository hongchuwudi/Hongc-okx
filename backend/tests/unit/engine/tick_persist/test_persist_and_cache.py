"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_persist_and_cache.py 持久化+缓存
描述: 验证 persist_tick 和 cache_signal 被调用
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_persist_and_cache_called(mock_engine, sample_account):
    sig = Signal(signal="BUY", confidence="HIGH", reason="test", stop_loss=95.0, take_profit=105.0)
    mock_engine.risk.record_tick_success = AsyncMock(return_value={})
    with patch("app.engine.loop.tick_persist.persist_tick", AsyncMock()) as mp, \
         patch("app.engine.loop.tick_persist.cache_signal", AsyncMock()) as mc, \
         patch("app.engine.loop.tick_persist.publish_event", AsyncMock()), \
         patch("app.agents.status.save_tick_agent_logs", AsyncMock()):
        from app.engine.loop.tick_persist import tick_persist_and_notify
        await tick_persist_and_notify(mock_engine, datetime.now(), 100.0, sample_account, None, sig, None)
    mp.assert_called_once(); mc.assert_called_once_with(sig)
