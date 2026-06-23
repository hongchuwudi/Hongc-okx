"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_normal.py 正常状态
描述: 熔断未触发时返回 True
"""
import pytest
@pytest.mark.asyncio
async def test_circuit_normal_returns_true(mock_engine):
    from app.engine.loop.tick_circuit import tick_check_circuit
    assert await tick_check_circuit(mock_engine) is True
