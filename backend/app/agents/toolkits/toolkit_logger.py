"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_logger.py 工具调用日志
描述: LangChain 回调处理器 — 记录每个 Agent 调了什么工具、传了什么参数、返回了什么

包含:
- 类: ToolCallLogger — 拦截 on_tool_start / on_tool_end 输出结构化日志
"""

from langchain_core.callbacks import BaseCallbackHandler
from app.logger import get_logger

logger = get_logger()


class ToolCallLogger(BaseCallbackHandler):
    """记录 Agent 工具调用的入参和返回值。"""

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        """工具被调起时记录参数。"""
        name = serialized.get("name", "unknown")
        # 截断过长入参
        inp = str(input_str)[:120]
        logger.info(f"  [{name}] 入参: {inp}")

    def on_tool_end(self, output: str, **kwargs):
        """工具返回时记录结果摘要。"""
        out = str(output)[:120]
        logger.info(f"          返回: {out}")

    def on_tool_error(self, error, **kwargs):
        """工具异常时记录。"""
        logger.error(f"          异常: {error}")
