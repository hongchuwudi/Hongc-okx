"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_factory_5_agents.py 5 Agent 工厂测试
描述: 验证 build_agents() 返回 5 个已编译 Agent 子图
"""

import sys
from unittest.mock import patch, MagicMock


def test_build_agents_returns_five_agents():
    """build_agents() 返回 5 个 Agent, 每个有 name 属性。"""
    with patch.dict(sys.modules, _mock_pandas_ta()), \
         patch('app.core.config.config.ai.deepseek_api_key', 'test-key'), \
         patch('app.agents.agent_factory.create_react_agent') as mock_create, \
         patch('app.agents.agent_factory.SystemMessage', MagicMock()), \
         patch('app.agents.agent_factory.get_prompt_sync', return_value="test"):
        mock_create.side_effect = lambda **kwargs: _make_agent(kwargs.get("name", "unknown"))

        from app.agents.agent_factory import build_agents
        agents = build_agents()
        assert isinstance(agents, dict)
        assert len(agents) == 5, f"期望 5 个 Agent, 实际 {len(agents)}"
        expected = {"scheduler", "analyst", "reviewer", "risk", "trader"}
        assert set(agents.keys()) == expected
        for name, agent in agents.items():
            assert hasattr(agent, 'name'), f"Agent {name} 缺少 name 属性"


def _mock_pandas_ta():
    """Mock pandas_ta 模块（Python 3.11 无兼容版本）。"""
    fake_ta = MagicMock()
    fake_ta.rsi = MagicMock(return_value=MagicMock())
    fake_ta.macd = MagicMock(return_value=MagicMock())
    fake_ta.sma = MagicMock(return_value=MagicMock())
    fake_ta.bbands = MagicMock(return_value=MagicMock())
    fake_ta.atr = MagicMock(return_value=MagicMock())
    return {"pandas_ta": fake_ta}


def _make_agent(name: str):
    ag = MagicMock()
    ag.name = name
    return ag
