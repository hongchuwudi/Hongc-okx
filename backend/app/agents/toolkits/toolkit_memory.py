"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: memory_server.py 交易记忆工具
描述: 从 tools/memory 导入纯查询函数，包装为 LangChain @tool

包含:
- LangChain Tools: tools (3个)
"""

from langchain_core.tools import tool as lc_tool
from app.agents.toolkits.tools.toolkit_calc_memory import (
    get_trade_stats, get_recent_trades, get_lessons,
)

get_trade_stats = lc_tool(get_trade_stats)
get_recent_trades = lc_tool(get_recent_trades)
get_lessons = lc_tool(get_lessons)

tools = [get_trade_stats, get_recent_trades, get_lessons]
