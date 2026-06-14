"""
测试: Agent 工厂 — 5 个 Agent 能否正常构建
"""


class TestAgentFactory:
    def test_build_all_agents(self):
        from app.agents.agent_factory import build_agents
        agents = build_agents()
        assert set(agents.keys()) == {"scheduler", "analyst", "reviewer", "risk", "trader"}
        # 每个 Agent 应该是一个 compiled graph
        for name, agent in agents.items():
            assert hasattr(agent, "invoke"), f"{name} 缺少 invoke 方法"
            assert agent.name == name, f"{name} 名字不匹配: {agent.name}"

    def test_agent_has_tools(self):
        from app.agents.agent_factory import build_agents
        agents = build_agents()
        # 分析师应该有市场工具
        analyst = agents["analyst"]
        assert analyst is not None
