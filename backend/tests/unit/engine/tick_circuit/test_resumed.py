"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_resumed.py 冷却恢复
描述: 冷却期满自动恢复，返回 True
"""
import pytest
from unittest.mock import AsyncMock
@pytest.mark.asyncio
async def test_circuit_resumed_returns_true(mock_engine):
    mock_engine.risk.check_pause = AsyncMock(return_value={"resumed": True, "blocked": False})
    from app.engine.loop.tick_circuit import tick_check_circuit
    assert await tick_check_circuit(mock_engine) is True
