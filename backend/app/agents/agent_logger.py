"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: agent_logger.py 工具调用日志+推送
描述: LangChain 回调处理器 — 记录工具调用 + 推送 agent_tool_call 到状态总线

包含:
- 类: ToolCallLogger — 拦截 on_tool_start/on_tool_end，日志+推送
- 函数: set_current_agent — 设置当前 Agent（线程本地存储，避免并行竞态）
- 变量: _tls — 线程本地存储，暂存当前 Agent 名和工具名
"""

import asyncio
import threading

from langchain_core.callbacks import BaseCallbackHandler
from app.core.logger import get_logger

logger = get_logger()

# 线程本地存储：每个线程独立维护当前 Agent 名和工具名，避免并行竞态
_tls = threading.local()


# 设置当前线程正在运行的 Agent 名称。
def set_current_agent(name: str):
    _tls.agent = name


# 获取当前线程的 Agent 名称。
def _current_agent() -> str:
    return getattr(_tls, "agent", "")


# 记录工具调用的入参和返回值，并推送到 Agent 状态总线。
class ToolCallLogger(BaseCallbackHandler):

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None):
        self._loop = loop  # 可在构造后由 coordinator 设置

    # 工具被调起时记录参数（不推送，等 on_tool_end 一次性推送结果）
    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        name = serialized.get("name", "unknown")
        inp = str(input_str)[:500]
        _tls.tool = name  # 暂存工具名，供 on_tool_end 使用
        logger.info(f"  [{name}] 入参: {inp}")

    # 工具返回时记录结果并推送。
    def on_tool_end(self, output: str, **kwargs):
        name = getattr(_tls, "tool", "")
        out = str(output)[:500]
        logger.info(f"          返回: {out}")
        self._push("agent_tool_call", tool=name, args="", result=out)

    # 工具异常时记录错误并推送。
    def on_tool_error(self, error, **kwargs):
        name = getattr(_tls, "tool", "")
        logger.error(f"          异常: {error}")
        self._push("agent_tool_call", tool=name, args="", result=f"ERROR: {error}")

    # 异步推送事件到状态总线（跨线程安全）。
    def _push(self, event_type: str, **kwargs):
        if self._loop is None:
            return
        try:
            from app.agents.agent_status import publish_agent_status

            async def _do():
                await publish_agent_status(event_type, _current_agent(), **kwargs)

            asyncio.run_coroutine_threadsafe(_do(), self._loop)
        except Exception:
            pass
