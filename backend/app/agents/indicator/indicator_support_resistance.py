"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: indicator_support_resistance.py 支撑阻力计算
描述: 静态 + 动态（布林带）支撑阻力位计算

包含:
- 函数: support_resistance — 返回支撑阻力位字典
"""

import pandas as pd


def support_resistance(df: pd.DataFrame, lookback: int = 20) -> dict:
    """静态 + 动态（布林带）支撑阻力。

    返回: static_resistance、static_support、dynamic_resistance、dynamic_support、
          price_vs_resistance（距阻力百分比）、price_vs_support（距支撑百分比）。
    """
    try:
        recent_high = float(df["high"].tail(lookback).max())
        recent_low = float(df["low"].tail(lookback).min())
        price = float(df["close"].iloc[-1])
        bb_upper = float(df["bb_upper"].iloc[-1])
        bb_lower = float(df["bb_lower"].iloc[-1])
        return {
            "static_resistance": recent_high,
            "static_support": recent_low,
            "dynamic_resistance": bb_upper,
            "dynamic_support": bb_lower,
            "price_vs_resistance": ((recent_high - price) / price) * 100,
            "price_vs_support": ((price - recent_low) / recent_low) * 100,
        }
    except Exception:
        return {}
