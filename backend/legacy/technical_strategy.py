"""
纯技术指标策略 — 不依赖任何外部 API，仅用 SMA + RSI + MACD 组合信号
"""
from typing import Dict, Optional

import pandas as pd

from base_strategy import BaseStrategy


class TechnicalStrategy(BaseStrategy):
    """基于技术指标的规则策略"""

    @property
    def name(self) -> str:
        return "TechnicalStrategy"

    def generate_signal(
        self,
        df: pd.DataFrame,
        current_position: Optional[Dict] = None,
        **kwargs,
    ) -> Dict:
        return _technical_signal(df, current_position)


def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """从原始 OHLCV 计算技术指标"""
    df = df.copy()

    # SMA
    df["sma_5"] = df["close"].rolling(window=5, min_periods=1).mean()
    df["sma_20"] = df["close"].rolling(window=20, min_periods=1).mean()
    df["sma_50"] = df["close"].rolling(window=50, min_periods=1).mean()

    # EMA / MACD
    df["ema_12"] = df["close"].ewm(span=12).mean()
    df["ema_26"] = df["close"].ewm(span=26).mean()
    df["macd"] = df["ema_12"] - df["ema_26"]
    df["macd_signal"] = df["macd"].ewm(span=9).mean()

    # RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    df = df.bfill().ffill()
    return df


def _technical_signal(
    df: pd.DataFrame, current_position: Optional[Dict] = None
) -> Dict:
    df = _calculate_indicators(df)
    last = df.iloc[-1]

    sma_5, sma_20, sma_50 = last["sma_5"], last["sma_20"], last["sma_50"]
    rsi, macd, macd_sig = last["rsi"], last["macd"], last["macd_signal"]
    price = last["close"]

    # 趋势判定
    bullish_trend = sma_5 > sma_20 > sma_50
    bearish_trend = sma_5 < sma_20 < sma_50
    macd_bullish = macd > macd_sig
    macd_bearish = macd < macd_sig

    # 默认
    signal = "HOLD"
    confidence = "LOW"
    reason = "趋势不明朗，保持观望"

    # 做多信号
    if bullish_trend and macd_bullish and rsi < 70:
        signal = "BUY"
        confidence = "HIGH" if rsi < 60 else "MEDIUM"
        reason = "均线多头排列 + MACD金叉"
    elif bullish_trend and macd_bullish:
        signal = "BUY"
        confidence = "MEDIUM"
        reason = "短期均线多头 + MACD偏多"
    elif sma_5 > sma_20 and rsi < 35:
        signal = "BUY"
        confidence = "LOW"
        reason = "短线反弹信号"

    # 做空信号
    elif bearish_trend and macd_bearish and rsi > 30:
        signal = "SELL"
        confidence = "HIGH" if rsi > 40 else "MEDIUM"
        reason = "均线空头排列 + MACD死叉"
    elif bearish_trend and macd_bearish:
        signal = "SELL"
        confidence = "MEDIUM"
        reason = "短期均线空头 + MACD偏空"
    elif sma_5 < sma_20 and rsi > 65:
        signal = "SELL"
        confidence = "LOW"
        reason = "短线回调信号"

    # 止盈止损计算
    if signal == "BUY":
        stop_loss = price * 0.985 if confidence == "HIGH" else price * 0.98
        take_profit = price * 1.03 if confidence == "HIGH" else price * 1.02
    elif signal == "SELL":
        stop_loss = price * 1.015 if confidence == "HIGH" else price * 1.02
        take_profit = price * 0.97 if confidence == "HIGH" else price * 0.98
    else:
        stop_loss = price * 0.98
        take_profit = price * 1.02

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": reason,
        "stop_loss": round(stop_loss, 2),
        "take_profit": round(take_profit, 2),
    }
