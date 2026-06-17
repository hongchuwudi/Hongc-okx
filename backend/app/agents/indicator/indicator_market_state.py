"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: indicator_market_state.py 市场状态分类
描述: 综合市场状态分类（趋势 + 波动率），输出状态标签和置信度

包含:
- 函数: market_state — 返回市场状态字典（state、confidence、atr_pct、trend_strength）
"""

import pandas as pd
from app.agents.indicator.indicator_atr import atr_pct


def market_state(df: pd.DataFrame) -> dict:
    """综合市场状态分类（趋势 + 波动率）。

    返回: state（状态标签）、confidence（置信度 0-1）、atr_pct、trend_strength。
    """
    try:
        last = df.iloc[-1]
        price = float(last["close"])
        sma_5 = float(last.get("sma_5", 0) or 0)
        sma_20 = float(last.get("sma_20", 0) or 0)
        sma_50 = float(last.get("sma_50", 0) or 0)
        atr = atr_pct(df)

        # 计算趋势强度（价格距离 SMA20 的百分比）
        trend_pct = abs(price - sma_20) / sma_20 * 100 if sma_20 > 0 else 0

        # 通过均线排列 + 价格偏离判断趋势
        if sma_5 > sma_20 > sma_50 and trend_pct > 0.5:
            ts, conf = "强上涨", 0.9
        elif sma_5 < sma_20 < sma_50 and trend_pct > 0.5:
            ts, conf = "强下跌", 0.9
        elif sma_5 > sma_20:
            ts, conf = "偏多", 0.65
        elif sma_5 < sma_20:
            ts, conf = "偏空", 0.65
        elif atr < 0.3 and trend_pct < 0.3:
            ts, conf = "震荡", 0.5
        else:
            ts, conf = "弱趋势", 0.5

        if atr > 3:
            state = f"高波动{ts}"
        elif atr < 0.5:
            state = "低波动震荡"
        else:
            state = ts

        return {"state": state, "confidence": conf, "atr_pct": atr, "trend_strength": ts}
    except Exception:
        return {"state": "未知", "confidence": 0.5, "atr_pct": 2.0, "trend_strength": "未知"}
