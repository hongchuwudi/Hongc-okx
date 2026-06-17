"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: indicator_rsi.py RSI 计算
描述: 计算简易 RSI（相对强弱指数）值

包含:
- 函数: calc_rsi — 计算当前价格的 RSI 值
"""

import pandas as pd


def calc_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """计算简易 RSI 值。计算失败返回中性值 50.0。"""
    try:
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
        rs = gain / loss
        return float(100.0 - (100.0 / (1.0 + rs.iloc[-1])))
    except Exception:
        return 50.0
