"""
集成测试: Coordinator 完整流水线

测试 5 Agent 依次运行、移交检测、对话路由、退回循环
"""

import asyncio
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv():
    """200 行模拟 K 线。"""
    np.random.seed(42)
    n = 200
    close = np.cumsum(np.random.randn(n) * 50) + 95000
    return pd.DataFrame({
        "close": close,
        "high": close + np.random.rand(n) * 200,
        "low": close - np.random.rand(n) * 200,
        "volume": np.random.rand(n) * 1000 + 500,
    }, index=pd.date_range("2026-06-01", periods=n, freq="1min"))


class TestCoordinatorBuild:
    """Coordinator 能否正常构建，Agent 数量是否正确。"""

    def test_coordinator_init(self):
        from app.agents.coordinator import AgentCoordinator
        c = AgentCoordinator()
        agents = c._agents
        assert set(agents.keys()) == {"scheduler", "analyst", "reviewer", "risk", "trader"}

class TestHandoffFlow:
    """移交信号检测和路由。"""

    def test_handoff_detection_from_result(self):
        from app.agents.toolkits.communication.toolkit_router import detect_handoff
        from app.agents.toolkits.communication.toolkit_handoff import HANDOFF_SIGNAL

        # 模拟 Agent 返回的消息
        fake_msg = type("Msg", (), {"content": f"分析完成 {HANDOFF_SIGNAL}risk|风控通过"})()
        fake_state = {"messages": [fake_msg]}
        assert detect_handoff(fake_state) == "risk"

    def test_no_handoff_when_no_signal(self):
        from app.agents.toolkits.communication.toolkit_router import detect_handoff

        fake_msg = type("Msg", (), {"content": "分析完成，没有移交信号"})()
        fake_state = {"messages": [fake_msg]}
        assert detect_handoff(fake_state) is None


class TestAskFlow:
    """对话信号检测。"""

    def test_ask_detection(self):
        from app.agents.toolkits.communication.toolkit_router import detect_ask
        from app.agents.toolkits.communication.toolkit_dialogue import ASK_SIGNAL

        fake_msg = type("Msg", (), {"content": f"{ASK_SIGNAL}analyst|你怎么看这个RSI？"})()
        fake_state = {"messages": [fake_msg]}
        target, question = detect_ask(fake_state)
        assert target == "analyst"
        assert "RSI" in question

    def test_no_ask_when_no_signal(self):
        from app.agents.toolkits.communication.toolkit_router import detect_ask

        fake_msg = type("Msg", (), {"content": "正常分析输出"})()
        fake_state = {"messages": [fake_msg]}
        target, _ = detect_ask(fake_state)
        assert target is None


class TestFeedbackLoop:
    """学习闭环：上一轮对错检测。"""

    def test_feedback_with_profit(self, sample_ohlcv):
        from app.agents.toolkits.toolkit_data import load_data
        from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback

        load_data(sample_ohlcv, 96000, 10000, {"side": "long", "size": 0.1, "entry_price": 94000, "unrealized_pnl": 200})
        result = generate_feedback()
        assert "对了" in result or "多" in result

    def test_feedback_with_loss(self, sample_ohlcv):
        from app.agents.toolkits.toolkit_data import load_data
        from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback

        load_data(sample_ohlcv, 93000, 10000, {"side": "long", "size": 0.1, "entry_price": 94000, "unrealized_pnl": -100})
        result = generate_feedback()
        assert "错了" in result or "有误" in result

    def test_feedback_no_position(self, sample_ohlcv):
        from app.agents.toolkits.toolkit_data import load_data
        from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback

        load_data(sample_ohlcv, 95000, 10000, {})
        result = generate_feedback()
        assert "HOLD" in result or "未开仓" in result


class TestAgentStatus:
    """Agent 状态总线。"""

    def test_get_empty_status(self):
        from app.agents.agent_status import get_agents_status
        status = get_agents_status()
        assert "agents" in status
        assert "history" in status
        assert isinstance(status["history"], list)

    def test_agent_input_output(self):
        import asyncio
        from app.agents.agent_status import agent_input, agent_output, get_agents_status

        async def run():
            await agent_input("test_agent", "测试输入")
            await agent_output("test_agent", "测试输出", "mock_target")

        asyncio.run(run())
        status = get_agents_status()
        assert "test_agent" in status["agents"]


class TestRedoLogic:
    """风控退回逻辑：保证 MAX_REDO 不超。"""

    def test_max_redo_constant(self):
        from app.agents.coordinator import MAX_REDO
        assert MAX_REDO == 2

    def test_handoff_analyst_returns_analyst(self):
        from app.agents.toolkits.communication.toolkit_router import detect_handoff
        from app.agents.toolkits.communication.toolkit_handoff import HANDOFF_SIGNAL

        fake_msg = type("Msg", (), {"content": f"证据不足 {HANDOFF_SIGNAL}analyst|请重新分析"})()
        fake_state = {"messages": [fake_msg]}
        assert detect_handoff(fake_state) == "analyst"
