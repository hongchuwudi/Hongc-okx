"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: technical.py 中文名
描述: 纯技术指标策略 — 基于 SMA、RSI、MACD 等指标生成信号，不依赖外部 API

包含:
- 类: TechnicalStrategy — 技术指标策略实现
- 函数: _calculate_indicators — 计算技术指标
- 函数: _technical_signal — 根据指标组合生成交易信号
"""

from typing import Dict, Optional

import pandas as pd

from app.strategies.base import BaseStrategy
from app.services.agent.agent_coordinator_service import get_indicator_service

IndicatorService = get_indicator_service()


# 纯技术指标策略 — 使用 SMA、RSI、MACD 等经典指标生成信号
class TechnicalStrategy(BaseStrategy):

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


# 计算所有技术指标（SMA、RSI、MACD、布林带等）
def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    return IndicatorService.calculate_all(df)


# 根据技术指标组合生成交易信号
def _technical_signal(
    df: pd.DataFrame, current_position: Optional[Dict] = None
) -> Dict:
    df = _calculate_indicators(df)
    last = df.iloc[-1]
    # 提取关键指标值
    sma_5, sma_20, sma_50 = last["sma_5"], last["sma_20"], last["sma_50"]
    rsi, macd, macd_sig = last["rsi"], last["macd"], last["macd_signal"]
    price = last["close"]

    # 趋势判断
    bullish_trend = sma_5 > sma_20 > sma_50        # 多头排列
    bearish_trend = sma_5 < sma_20 < sma_50        # 空头排列
    macd_bullish = macd > macd_sig                  # MACD 金叉
    macd_bearish = macd < macd_sig                  # MACD 死叉

    signal = "HOLD"
    confidence = "LOW"
    reason = "趋势不明朗，保持观望"

    # 信号生成规则 — 放宽条件，以 SMA 交叉为核心
    sma_cross_up = sma_5 > sma_20 and df["sma_5"].iloc[-2] <= df["sma_20"].iloc[-2]  # 金叉
    sma_cross_down = sma_5 < sma_20 and df["sma_5"].iloc[-2] >= df["sma_20"].iloc[-2]  # 死叉

    if sma_cross_up and macd_bullish and rsi < 70:
        signal = "BUY"
        confidence = "HIGH" if rsi < 55 else "MEDIUM"
        reason = "SMA5上穿SMA20 + MACD金叉"
    elif sma_cross_up:
        signal = "BUY"
        confidence = "MEDIUM"
        reason = "SMA5上穿SMA20（短期趋势转多）"
    elif bullish_trend and macd_bullish:
        signal = "BUY"
        confidence = "LOW"
        reason = "均线多头 + MACD偏多"
    elif rsi < 30:
        signal = "BUY"
        confidence = "LOW"
        reason = "RSI超卖反弹信号"
    elif sma_cross_down and macd_bearish and rsi > 30:
        signal = "SELL"
        confidence = "HIGH" if rsi > 45 else "MEDIUM"
        reason = "SMA5下穿SMA20 + MACD死叉"
    elif sma_cross_down:
        signal = "SELL"
        confidence = "MEDIUM"
        reason = "SMA5下穿SMA20（短期趋势转空）"
    elif bearish_trend and macd_bearish:
        signal = "SELL"
        confidence = "LOW"
        reason = "均线空头 + MACD偏空"
    elif rsi > 70:
        signal = "SELL"
        confidence = "LOW"
        reason = "RSI超买回调信号"

    # 根据信号和信心水平设置止盈止损
    if signal == "BUY":
        stop_loss = price * 0.97 if confidence == "HIGH" else price * 0.975
        take_profit = price * 1.04 if confidence == "HIGH" else price * 1.025
    elif signal == "SELL":
        stop_loss = price * 1.03 if confidence == "HIGH" else price * 1.025
        take_profit = price * 0.96 if confidence == "HIGH" else price * 0.975
    else:
        stop_loss = price * 0.98
        take_profit = price * 1.02

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": reason,
        "stop_loss": float(round(stop_loss, 2)),
        "take_profit": float(round(take_profit, 2)),
    }
