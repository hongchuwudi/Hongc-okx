"""
集成测试: Coordinator 完整流水线

测试 5 Agent 依次运行、移交检测、对话路由、退回循环
"""

import asyncio
import numpy as np
import pandas as pd
import pytest


# 200 行模拟 K 线。
@pytest.fixture
def sample_ohlcv():
    np.random.seed(42)
    n = 200
    close = np.cumsum(np.random.randn(n) * 50) + 95000
    return pd.DataFrame({
        "close": close,
        "high": close + np.random.rand(n) * 200,
        "low": close - np.random.rand(n) * 200,
        "volume": np.random.rand(n) * 1000 + 500,
    }, index=pd.date_range("2026-06-01", periods=n, freq="1min"))


# Coordinator 能否正常构建，Agent 数量是否正确。
class TestCoordinatorBuild:

    def test_coordinator_init(self):
        from app.agents.coordinators.coordinator_5 import AgentCoordinator
        c = AgentCoordinator()
        agents = c._agents
        assert set(agents.keys()) == {"scheduler", "analyst", "reviewer", "risk", "trader"}

# 移交信号检测和路由。
class TestHandoffFlow:

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


# 对话信号检测。
class TestAskFlow:

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


# 学习闭环：上一轮对错检测。
class TestFeedbackLoop:

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


# Agent 状态总线。
class TestAgentStatus:

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


# 风控退回逻辑：保证 MAX_REDO 不超。
class TestRedoLogic:

    def test_max_redo_constant(self):
        from app.agents.coordinators.coordinator_5 import MAX_REDO
        assert MAX_REDO == 2

    def test_handoff_analyst_returns_analyst(self):
        from app.agents.toolkits.communication.toolkit_router import detect_handoff
        from app.agents.toolkits.communication.toolkit_handoff import HANDOFF_SIGNAL

        fake_msg = type("Msg", (), {"content": f"证据不足 {HANDOFF_SIGNAL}analyst|请重新分析"})()
        fake_state = {"messages": [fake_msg]}
        assert detect_handoff(fake_state) == "analyst"


# 3 Agent 协调器构建验证。
class TestCoordinator3Build:

    def test_coordinator3_init(self):
        from app.agents.coordinators.coordinator_3 import AgentCoordinator3
        c = AgentCoordinator3()
        agents = c._agents
        assert set(agents.keys()) == {"super_analyst", "risk", "trader"}

    def test_build_agents_3_keys(self):
        from app.agents.agent_factory import build_agents_3
        agents = build_agents_3()
        assert set(agents.keys()) == {"super_analyst", "risk", "trader"}

    def test_super_analyst_agent_built(self):
        from app.agents.agent_factory import build_agents_3
        agents = build_agents_3()
        sa = agents["super_analyst"]
        # 验证编译后的 Agent 有必要的属性
        assert sa is not None
        assert hasattr(sa, "invoke")
        # coordinator 能正常实例化
        from app.agents.coordinators.coordinator_3 import AgentCoordinator3
        c = AgentCoordinator3()
        assert c._super_analyst is not None
        assert c._risk is not None
        assert c._trader is not None


# 3 Agent 移交信号检测。
class TestCoordinator3Handoff:

    def test_handoff_to_super_analyst(self):
        from app.agents.toolkits.communication.toolkit_router import detect_handoff
        from app.agents.toolkits.communication.toolkit_handoff import HANDOFF_SIGNAL

        fake_msg = type("Msg", (), {"content": f"需要重新分析 {HANDOFF_SIGNAL}super_analyst|证据不足"})()
        fake_state = {"messages": [fake_msg]}
        assert detect_handoff(fake_state) == "super_analyst"

    def test_super_analyst_handoff_to_risk(self):
        from app.agents.toolkits.communication.toolkit_router import detect_handoff
        from app.agents.toolkits.communication.toolkit_handoff import HANDOFF_SIGNAL

        fake_msg = type("Msg", (), {"content": f"分析完成 {HANDOFF_SIGNAL}risk|请评估风险"})()
        fake_state = {"messages": [fake_msg]}
        assert detect_handoff(fake_state) == "risk"


# 1 Agent Solo 构建验证。
class TestCoordinatorSoloBuild:

    def test_coordinator_solo_init(self):
        from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
        c = AgentCoordinatorSolo()
        assert c._agent is not None

    def test_build_agent_solo(self):
        from app.agents.agent_factory import build_agent_solo
        agent = build_agent_solo()
        assert agent is not None
        assert hasattr(agent, "invoke")
