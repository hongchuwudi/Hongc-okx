"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_agent_mode_tech.py 切换 tech
描述: 切换到 tech 模式禁用 AI
"""
import pytest
from unittest.mock import AsyncMock, patch
@pytest.mark.asyncio
async def test_switch_to_tech(mock_engine):
    mock_engine._last_mode = "5_agent"
    with patch("app.engine.runtime.runtime_agent_mode.get_runtime_async", AsyncMock(return_value="tech")):
        from app.engine.runtime.runtime_agent_mode import _sync_agent_mode
        await _sync_agent_mode(mock_engine)
    assert mock_engine.use_multi_agent is False and mock_engine.coordinator is None
    assert "技术指标" in mock_engine.agent_mode_display
