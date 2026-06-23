"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_stopped_blocks.py 熔断停止
描述: 熔断已停止时返回 False
"""
import pytest
from unittest.mock import AsyncMock
@pytest.mark.asyncio
async def test_circuit_stopped_returns_false(mock_engine):
    mock_engine.risk.get_circuit_state = AsyncMock(return_value={"stopped": True})
    from app.engine.loop.tick_circuit import tick_check_circuit
    assert await tick_check_circuit(mock_engine) is False
