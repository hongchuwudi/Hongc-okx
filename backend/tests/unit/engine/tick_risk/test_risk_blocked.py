"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_risk_blocked.py 风控拦截
描述: 风控拦截返回 False
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engine.result.signal import Signal

@pytest.mark.asyncio
async def test_risk_blocked_returns_false(mock_engine, sample_account):
    mock_engine.risk.check = AsyncMock(return_value=MagicMock(passed=False, reason="日亏损超限"))
    from app.engine.loop.tick_risk import tick_check_risk
    sig = Signal(signal="BUY", confidence="HIGH")
    assert await tick_check_risk(mock_engine, sig, sample_account, None, 100.0) is False
