"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_event_payload.py 推送事件
描述: WebSocket 推送 tick_complete 事件字段完整
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_event_has_correct_fields(mock_engine, sample_account):
    sig = Signal(signal="SELL", confidence="LOW", reason="回调", stop_loss=102.0, take_profit=96.0)
    mock_engine.risk.record_tick_success = AsyncMock(return_value={})
    with patch("app.engine.loop.tick_persist.persist_tick", AsyncMock()), \
         patch("app.engine.loop.tick_persist.cache_signal", AsyncMock()), \
         patch("app.engine.loop.tick_persist.publish_event", AsyncMock()) as mp, \
         patch("app.agents.status.save_tick_agent_logs", AsyncMock()):
        from app.engine.loop.tick_persist import tick_persist_and_notify
        await tick_persist_and_notify(mock_engine, datetime(2026,6,23,10,30), 99.5, sample_account, None, sig, None)
    e = mp.call_args.args[0]
    assert e["type"] == "tick_complete" and e["btc_price"] == 99.5
    assert e["signal"] == "SELL" and e["confidence"] == "LOW"
