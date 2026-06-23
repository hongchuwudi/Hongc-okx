"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_factory_solo.py Solo 工厂测试
描述: 验证 build_agent_solo() 返回单个已编译 Agent
"""

from unittest.mock import patch, MagicMock


def test_build_agent_solo_returns_one_agent():
    """build_agent_solo() 返回单个 Agent 且 name='solo'。"""
    with patch('app.core.config.config.ai.deepseek_api_key', 'test-key'), \
         patch('app.agents.agent_factory.create_react_agent') as mock_create, \
         patch('app.agents.agent_factory.SystemMessage', MagicMock()), \
         patch('app.agents.agent_factory.get_prompt_sync', return_value="test"):
        mock_create.return_value = _make_agent("solo")

        from app.agents.agent_factory import build_agent_solo
        agent = build_agent_solo()
        assert agent is not None, "build_agent_solo 返回 None"
        assert hasattr(agent, 'name'), "Solo Agent 缺少 name 属性"
        assert agent.name == "solo", f"Solo Agent name='{agent.name}'"


def _make_agent(name: str):
    ag = MagicMock()
    ag.name = name
    return ag
