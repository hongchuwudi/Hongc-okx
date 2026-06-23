"""
测试: 5 Agent Swarm 的 _base() 方法
"""

from unittest.mock import patch, MagicMock


def test_base_returns_required_keys():
    """_base() 必须返回 messages / remaining_steps / price / equity。"""
    from app.agents.coordinators.coordinator_5 import AgentCoordinator
    with patch.object(AgentCoordinator, '__init__', lambda self: None):
        coordinator = AgentCoordinator.__new__(AgentCoordinator)
        coordinator._logger = MagicMock()

    with patch('app.agents.toolkits.toolkit_data._position', return_value=None), \
         patch('app.agents.coordinators.coordinator_5.get_runtime', return_value=10):
        base = coordinator._base(100.0, 10000.0)

    assert "messages" in base
    assert base["remaining_steps"] == 10
    assert base["price"] == 100.0
    assert base["equity"] == 10000.0


def test_base_context_contains_price_and_equity():
    """上下文文本包含价格和权益。"""
    from app.agents.coordinators.coordinator_5 import AgentCoordinator
    with patch.object(AgentCoordinator, '__init__', lambda self: None):
        coordinator = AgentCoordinator.__new__(AgentCoordinator)
        coordinator._logger = MagicMock()

    with patch('app.agents.toolkits.toolkit_data._position', return_value=None), \
         patch('app.agents.coordinators.coordinator_5.get_runtime', return_value=10):
        base = coordinator._base(100.0, 10000.0)

    context = base["messages"][0].content
    assert "100.00" in context
    assert "10,000" in context
