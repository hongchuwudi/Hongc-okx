"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_logger.py 工具调用日志+推送
描述: LangChain 回调处理器 — 记录工具调用 + 推送 agent_tool_call 到状态总线

包含:
- 类: ToolCallLogger — 拦截 on_tool_start/on_tool_end，日志+推送
"""

import asyncio

from langchain_core.callbacks import BaseCallbackHandler
from app.logger import get_logger

logger = get_logger()


class ToolCallLogger(BaseCallbackHandler):
    """记录工具调用的入参和返回值，并推送到 Agent 状态总线。"""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None):
        self._loop = loop or asyncio.get_event_loop()

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        """工具被调起时记录参数并推送。"""
        name = serialized.get("name", "unknown")
        inp = str(input_str)[:120]
        logger.info(f"  [{name}] 入参: {inp}")
        self._push("agent_tool_call", tool_name=name, args=inp, result="")

    def on_tool_end(self, output: str, **kwargs):
        """工具返回时记录结果并推送。"""
        out = str(output)[:120]
        logger.info(f"          返回: {out}")
        self._push("agent_tool_call", tool_name="", args="", result=out)

    def on_tool_error(self, error, **kwargs):
        logger.error(f"          异常: {error}")
        self._push("agent_tool_call", tool_name="", args="", result=f"ERROR: {error}")

    def _push(self, event_type: str, **kwargs):
        """异步推送事件到状态总线（跨线程安全）。"""
        try:
            from app.agents.toolkits.toolkit_agent_status import publish_agent_status

            async def _do():
                await publish_agent_status(event_type, _current_agent, **kwargs)

            asyncio.run_coroutine_threadsafe(_do(), self._loop)
        except Exception:
            pass


# coordinator 设置当前运行的 Agent 名称
_current_agent = ""


def set_current_agent(name: str):
    global _current_agent
    _current_agent = name
