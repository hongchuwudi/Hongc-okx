"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: agent_status_hooks.py Agent 生命周期钩子
描述: Agent 运行生命周期的事件钩子 — input / output / tool_call

包含:
- 函数: agent_input — 标记 Agent 开始运行（记录输入摘要）
- 函数: agent_output — 标记 Agent 完成运行（记录输出摘要 + 移交目标）
- 函数: agent_tool_call — 标记 Agent 调用了工具
"""

from app.agents.status.agent_status_publish import publish_agent_status


async def agent_input(agent_name: str, summary: str):
    """Agent 开始运行：推送收到的输入摘要。"""
    await publish_agent_status("agent_input", agent_name, input=summary)


async def agent_output(agent_name: str, summary: str, handoff: str | None = None):
    """Agent 完成运行：推送输出摘要和移交目标。"""
    await publish_agent_status("agent_output", agent_name,output=summary,handoff=handoff or "none")


async def agent_tool_call(agent_name: str, tool_name: str, args: str, result: str):
    """Agent 调用了工具：推送工具名、入参、返回值。"""
    await publish_agent_status("agent_tool_call", agent_name,tool=tool_name, args=args, result=result)
