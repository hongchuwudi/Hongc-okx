"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_no_update.py 未更新
描述: pm 返回 updated=False 时保持原 sl/tp
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_keeps_original_when_not_updated(mock_engine):
    sig = Signal(signal="SELL", stop_loss=105.0, take_profit=95.0)
    ind = MagicMock(); ind.atr_pct.return_value = 0.01
    mock_engine.position_manager.update = AsyncMock(return_value={"updated":False,"stop_loss":999,"take_profit":1})
    from app.engine.loop.tick_position import tick_manage_position
    result = await tick_manage_position(mock_engine, {"side":"short","size":0.2}, 100.0, MagicMock(), sig, ind)
    assert result.stop_loss == 105.0 and result.take_profit == 95.0
