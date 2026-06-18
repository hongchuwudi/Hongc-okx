"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: test_tick_circuit.py 熔断检查测试
描述: 验证 tick_circuit 的暂停/停止/正常三种状态判断

包含:
- TestCircuitNormal — 正常状态，返回 True
- TestCircuitPaused — 熔断暂停，返回 False
- TestCircuitStopped — 熔断停止，返回 False
"""

import pytest
from unittest.mock import AsyncMock


class TestCircuitNormal:
    """熔断未触发时，返回 True 继续执行。"""

    @pytest.mark.asyncio
    async def test_circuit_ok(self, mock_engine):
        from app.engine.loop.tick_circuit import tick_check_circuit
        result = await tick_check_circuit(mock_engine)
        assert result is True

    @pytest.mark.asyncio
    async def test_circuit_resumed_logs(self, mock_engine):
        """冷却期满自动恢复。"""
        mock_engine.risk.check_pause = AsyncMock(return_value={
            "resumed": True, "blocked": False
        })
        from app.engine.loop.tick_circuit import tick_check_circuit
        result = await tick_check_circuit(mock_engine)
        assert result is True


class TestCircuitPaused:
    """熔断暂停时返回 False，阻止 tick 继续。"""

    @pytest.mark.asyncio
    async def test_circuit_paused_blocks(self, mock_engine):
        mock_engine.risk.check_pause = AsyncMock(return_value={
            "resumed": False, "blocked": True, "remaining_s": 120
        })
        from app.engine.loop.tick_circuit import tick_check_circuit
        result = await tick_check_circuit(mock_engine)
        assert result is False


class TestCircuitStopped:
    """熔断停止时返回 False，阻止 tick 继续。"""

    @pytest.mark.asyncio
    async def test_circuit_stopped_blocks(self, mock_engine):
        mock_engine.risk.get_circuit_state = AsyncMock(return_value={
            "stopped": True
        })
        from app.engine.loop.tick_circuit import tick_check_circuit
        result = await tick_check_circuit(mock_engine)
        assert result is False
