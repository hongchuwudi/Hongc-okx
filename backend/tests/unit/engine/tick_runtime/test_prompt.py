"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_prompt.py 提示词热重载
描述: 提示词版本变化时重建 coordinator
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
@pytest.mark.asyncio
async def test_prompt_version_change_rebuilds(mock_engine):
    mock_engine.use_multi_agent = True
    mock_engine.coordinator = MagicMock()
    mock_engine._last_prompt_version = 1
    mock_engine._last_mode = "5_agent"
    fc = MagicMock()
    with patch("app.agents.prompts.get_prompt_version", AsyncMock(return_value=2)), \
         patch("app.services.agent.agent_coordinator_service.create_coordinator", return_value=fc):
        from app.engine.runtime.runtime_prompt import _sync_prompt
        await _sync_prompt(mock_engine)
    assert mock_engine._last_prompt_version == 2 and mock_engine.coordinator is fc

@pytest.mark.asyncio
async def test_prompt_noop_not_multi_agent(mock_engine):
    mock_engine.use_multi_agent = False
    mock_engine._last_prompt_version = 1
    from app.engine.runtime.runtime_prompt import _sync_prompt
    await _sync_prompt(mock_engine)
    assert mock_engine._last_prompt_version == 1

@pytest.mark.asyncio
async def test_prompt_unchanged_noop(mock_engine):
    mock_engine.use_multi_agent = True
    mock_engine.coordinator = MagicMock()
    mock_engine._last_prompt_version = 1
    old = mock_engine.coordinator
    with patch("app.agents.prompts.get_prompt_version", AsyncMock(return_value=1)):
        from app.engine.runtime.runtime_prompt import _sync_prompt
        await _sync_prompt(mock_engine)
    assert mock_engine.coordinator is old
