"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: indicator/ 统一技术指标计算服务
描述: 统一技术指标服务 — 全项目唯一指标计算来源

目录结构:
- indicator_calculator.py        — calculate_all() + latest_indicators()
- indicator_atr.py               — atr_pct()
- indicator_rsi.py               — calc_rsi()
- indicator_trend.py             — trend_analysis()
- indicator_support_resistance.py — support_resistance()
- indicator_market_state.py      — market_state()

包含:
- 类: IndicatorService — 静态方法集合，向后兼容的统一入口
"""

from app.agents.indicator.indicator_calculator import calculate_all, latest_indicators
from app.agents.indicator.indicator_atr import atr_pct
from app.agents.indicator.indicator_rsi import calc_rsi
from app.agents.indicator.indicator_trend import trend_analysis
from app.agents.indicator.indicator_support_resistance import support_resistance
from app.agents.indicator.indicator_market_state import market_state


# 静态方法集合 — 向后兼容，所有策略和 Agent 统一调用此处计算
class IndicatorService:

    calculate_all = staticmethod(calculate_all)
    latest_indicators = staticmethod(latest_indicators)
    atr_pct = staticmethod(atr_pct)
    calc_rsi = staticmethod(calc_rsi)
    trend_analysis = staticmethod(trend_analysis)
    support_resistance = staticmethod(support_resistance)
    market_state = staticmethod(market_state)
