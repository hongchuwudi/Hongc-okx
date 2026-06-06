"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: market_server.py 行情工具
描述: 从 tools/indicators 导入纯计算函数，包装为 LangChain @tool

包含:
- LangChain Tools: tools (8个)
"""

from langchain_core.tools import tool as lc_tool
from app.agents.toolkits.tools.toolkit_calc_indicator import (
    get_price, calc_rsi, calc_macd, calc_sma, calc_bollinger, calc_atr,
    calc_volume_ratio, calc_trend,
)

get_price = lc_tool(get_price)
calculate_rsi = lc_tool(calc_rsi)
calculate_macd = lc_tool(calc_macd)
calculate_sma = lc_tool(calc_sma)
calculate_bollinger = lc_tool(calc_bollinger)
calculate_atr = lc_tool(calc_atr)
get_volume_ratio = lc_tool(calc_volume_ratio)
get_trend_analysis = lc_tool(calc_trend)

tools = [get_price, calculate_rsi, calculate_macd, calculate_sma,
         calculate_bollinger, calculate_atr, get_volume_ratio, get_trend_analysis]
