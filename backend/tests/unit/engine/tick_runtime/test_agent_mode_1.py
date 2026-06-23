"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_agent_mode_1.py 切换 1 Agent
描述: 切换到 1_agent 急速模式
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
@pytest.mark.asyncio
async def test_switch_to_1_agent(mock_engine):
    mock_engine._last_mode = "tech"; mock_engine.coordinator = None
    fc = MagicMock()
    with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async", AsyncMock(return_value="1_agent")), \
         patch("app.engine.runtime.runtime_agent_mode.create_coordinator_solo", return_value=fc):
        from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
        await _sync_agent_mode(mock_engine)
    assert mock_engine.use_multi_agent is True and mock_engine.coordinator is fc

@pytest.mark.asyncio
async def test_switch_to_3_agent(mock_engine):
    mock_engine._last_mode = "1_agent"
    fc = MagicMock()
    with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async", AsyncMock(return_value="3_agent")), \
         patch("app.engine.runtime.runtime_agent_mode.create_coordinator_3", return_value=fc):
        from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
        await _sync_agent_mode(mock_engine)
    assert "3 Agent" in mock_engine.agent_mode_display

@pytest.mark.asyncio
async def test_switch_to_5_agent(mock_engine):
    mock_engine._last_mode = "1_agent"
    fc = MagicMock()
    with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async", AsyncMock(return_value="5_agent")), \
         patch("app.engine.runtime.runtime_agent_mode.create_coordinator", return_value=fc):
        from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
        await _sync_agent_mode(mock_engine)
    assert "5 Agent" in mock_engine.agent_mode_display

@pytest.mark.asyncio
async def test_mode_unchanged_noop(mock_engine):
    mock_engine._last_mode = "5_agent"; old = mock_engine.coordinator
    with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async", AsyncMock(return_value="5_agent")):
        from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
        await _sync_agent_mode(mock_engine)
    assert mock_engine.coordinator is old
