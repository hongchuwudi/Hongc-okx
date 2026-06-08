"""
Created: 2026-06-14
Author: hongchuwudi
Description: DeepSeek 策略指标函数 — 技术指标计算、趋势分析、市场状态识别

Contains:
- Function: calc_indicators — 计算所有技术指标
- Function: get_support_resistance_levels — 获取支撑阻力位
- Function: get_market_trend — 获取市场趋势分析
- Function: identify_market_state — 识别当前市场状态
"""

import pandas as pd
from app.services.agent.agent_coordinator_service import get_indicator_service

_indicator = get_indicator_service()


def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    return _indicator.calculate_all(df)


def get_support_resistance_levels(df: pd.DataFrame, lookback: int = 20) -> dict:
    return _indicator.support_resistance(df, lookback)


def get_market_trend(df: pd.DataFrame) -> dict:
    return _indicator.trend_analysis(df)


def identify_market_state(price_data: dict, tech_data: dict) -> dict:
    return _indicator.market_state(price_data["full_data"])
