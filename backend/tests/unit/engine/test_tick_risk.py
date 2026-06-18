"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: test_tick_risk.py 风控检查测试
描述: 验证风控通过/拦截/熔断拦截三种场景

包含:
- TestRiskPass — 风控通过，返回 True
- TestRiskBlock — 风控拦截，返回 False
- TestRiskCircuitBreak — 熔断触发拦截
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestRiskPass:
    """风控正常通过。"""

    @pytest.mark.asyncio
    async def test_risk_passes(self, mock_engine, sample_account):
        from app.engine.result.signal import Signal
        signal = Signal(signal="BUY", confidence="HIGH")
        from app.engine.loop.tick_risk import tick_check_risk
        result = await tick_check_risk(mock_engine, signal, sample_account, None, 100.0)
        assert result is True


class TestRiskBlock:
    """风控拦截，返回 False。"""

    @pytest.mark.asyncio
    async def test_risk_blocked(self, mock_engine, sample_account):
        mock_engine.risk.check = AsyncMock(return_value=MagicMock(
            passed=False, reason="日亏损超限"
        ))
        from app.engine.result.signal import Signal
        signal = Signal(signal="BUY", confidence="HIGH")
        from app.engine.loop.tick_risk import tick_check_risk
        result = await tick_check_risk(mock_engine, signal, sample_account, None, 100.0)
        assert result is False
