"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: agent_coordinator_service.py Agent 协调器服务
描述: 对 engine/strategies 层暴露的 Agent 协调器接口

包含:
- 类: AgentCoordinatorService — Coordinator/PositionManager/IndicatorService 的构建和访问
"""


# Agent 协调器服务 — 封装 AgentCoordinator、PositionManager、IndicatorService 的构建
class AgentCoordinatorService:

    # 构建 AgentCoordinator（5 Agent Swarm）
    def create_coordinator(self):
        from app.agents.coordinators.coordinator_5 import AgentCoordinator
        return AgentCoordinator()

    # 构建 AgentCoordinator3（3 Agent Swarm 快速模式）
    def create_coordinator_3(self):
        from app.agents.coordinators.coordinator_3 import AgentCoordinator3
        return AgentCoordinator3()

    # 构建 AgentCoordinatorSolo（1 Agent 急速模式）
    def create_coordinator_solo(self):
        from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
        return AgentCoordinatorSolo()

    # 构建 PositionManager（动态追踪止损）
    def create_position_manager(self, exchange, symbol: str):
        from app.services.trading.position_manager import PositionManager
        return PositionManager(exchange, symbol)

    # IndicatorService — 纯指标计算工具集
    def get_indicator_service(self):
        import app.agents.indicator as svc
        return svc

    # Agent 输出 JSON 解析器
    def parse_agent_output(self, text: str):
        from app.agents.parser import parse_agent_json_output
        return parse_agent_json_output(text)


# 全局单例
agent_coordinator_service = AgentCoordinatorService()

# 模块级包装函数 — 供 engine 直接 import 使用
create_coordinator = agent_coordinator_service.create_coordinator
create_coordinator_3 = agent_coordinator_service.create_coordinator_3
create_coordinator_solo = agent_coordinator_service.create_coordinator_solo
create_position_manager = agent_coordinator_service.create_position_manager
get_indicator_service = agent_coordinator_service.get_indicator_service
parse_agent_output = agent_coordinator_service.parse_agent_output
