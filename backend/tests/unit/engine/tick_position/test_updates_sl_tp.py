"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_updates_sl_tp.py 更新止盈止损
描述: pm 返回 updated=True 时应用新 sl/tp
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_updates_sl_tp_when_updated(mock_engine):
    sig = Signal(signal="BUY", stop_loss=95.0, take_profit=105.0)
    ind = MagicMock(); ind.atr_pct.return_value = 0.03
    mock_engine.position_manager.update = AsyncMock(return_value={"updated":True,"stop_loss":97.0,"take_profit":108.0})
    from app.engine.loop.tick_position import tick_manage_position
    result = await tick_manage_position(mock_engine, {"side":"long","size":0.1}, 100.0, MagicMock(), sig, ind)
    assert result.stop_loss == 97.0 and result.take_profit == 108.0
