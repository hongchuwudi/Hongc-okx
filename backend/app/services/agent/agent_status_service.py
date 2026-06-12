"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: agent_status_service.py Agent 状态服务
描述: 对 API 层暴露的 Agent 状态查询和事件推送接口

包含:
- 类: AgentStatusService — Agent 状态查询 + 事件推送
"""


# Agent 状态服务 — 封装 app.agents.agent_status 模块
class AgentStatusService:

    # 返回 5 个 Agent 的最新状态 + 最近 50 条事件历史
    def get_status(self) -> dict:
        from app.agents.agent_status import get_agents_status as _get
        return _get()

    # 推送 Agent 状态事件到 Redis Pub/Sub + 内存
    async def publish_event(self, event_type: str, agent_name: str, **kwargs):
        from app.agents.agent_status import publish_agent_status
        await publish_agent_status(event_type, agent_name, **kwargs)

    # Agent 开始运行
    async def agent_input(self, agent_name: str, summary: str):
        from app.agents.agent_status import agent_input as _fn
        await _fn(agent_name, summary)

    # Agent 完成运行
    async def agent_output(self, agent_name: str, summary: str, handoff: str | None = None):
        from app.agents.agent_status import agent_output as _fn
        await _fn(agent_name, summary, handoff)

    # Agent 工具调用
    async def agent_tool_call(self, agent_name: str, tool_name: str, args: str, result: str):
        from app.agents.agent_status import agent_tool_call as _fn
        await _fn(agent_name, tool_name, args, result)


# 全局单例
agent_status_service = AgentStatusService()
