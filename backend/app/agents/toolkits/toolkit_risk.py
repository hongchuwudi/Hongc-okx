"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: risk_server.py 风控工具
描述: 从 tools/risk 导入纯计算函数，包装为 LangChain @tool

包含:
- LangChain Tools: tools (3个)
"""

from langchain_core.tools import tool as lc_tool
from app.agents.toolkits.tools.toolkit_calc_risk import (
    evaluate_position_risk, calc_max_position, calc_sl_tp,
)

evaluate_position_risk = lc_tool(evaluate_position_risk)
calculate_max_position = lc_tool(calc_max_position)
calculate_sl_tp = lc_tool(calc_sl_tp)

tools = [evaluate_position_risk, calculate_max_position, calculate_sl_tp]
