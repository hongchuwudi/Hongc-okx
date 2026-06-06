"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: position_server.py 持仓工具
描述: 从 tools/position 导入纯查询函数，包装为 LangChain @tool

包含:
- LangChain Tools: tools (3个)
"""

from langchain_core.tools import tool as lc_tool
from app.agents.toolkits.tools.toolkit_calc_position import (
    get_position, get_account_summary, get_unrealized_pnl,
)

get_position = lc_tool(get_position)
get_account_summary = lc_tool(get_account_summary)
get_unrealized_pnl = lc_tool(get_unrealized_pnl)

tools = [get_position, get_account_summary, get_unrealized_pnl]
