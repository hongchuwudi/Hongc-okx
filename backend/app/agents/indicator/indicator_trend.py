"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: indicator_trend.py 趋势分析
描述: 基于均线和 MACD 的趋势分析（短期/中期/整体）

包含:
- 函数: trend_analysis — 返回趋势分析字典
"""

import pandas as pd


def trend_analysis(df: pd.DataFrame) -> dict:
    """返回趋势分析字典（兼容现有使用方）。

    包含：short_term（短期）、medium_term（中期）、macd 方向、overall（整体）、rsi_level。
    """
    try:
        last = df.iloc[-1]
        price = float(last["close"])
        sma_20 = float(last.get("sma_20", price))
        sma_50 = float(last.get("sma_50", price))
        macd = float(last.get("macd", 0) or 0)
        macd_signal = float(last.get("macd_signal", 0) or 0)

        short = "上涨" if price > sma_20 else "下跌"
        medium = "上涨" if price > sma_50 else "下跌"
        macd_dir = "bullish" if macd > macd_signal else "bearish"

        if short == "上涨" and medium == "上涨":
            overall = "强势上涨"
        elif short == "下跌" and medium == "下跌":
            overall = "强势下跌"
        else:
            overall = "震荡整理"

        return {
            "short_term": short,
            "medium_term": medium,
            "macd": macd_dir,
            "overall": overall,
            "rsi_level": float(last.get("rsi", 50)),
        }
    except Exception:
        return {"short_term": "N/A", "medium_term": "N/A", "macd": "N/A", "overall": "N/A", "rsi_level": 50}
