"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_paused_blocks.py 熔断暂停
描述: 熔断暂停时返回 False
"""
import pytest
from unittest.mock import AsyncMock
@pytest.mark.asyncio
async def test_circuit_paused_returns_false(mock_engine):
    mock_engine.risk.check_pause = AsyncMock(return_value={"resumed": False, "blocked": True, "remaining_s": 120})
    from app.engine.loop.tick_circuit import tick_check_circuit
    assert await tick_check_circuit(mock_engine) is False
