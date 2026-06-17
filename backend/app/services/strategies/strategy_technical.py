"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: strategy_technical.py 技术指标策略
描述: 5 信号打分制决策树 — 参考 PA_Agent 的二元决策树设计，不依赖外部 API

信号打分（每项 +1 / 0 / -1）:
  1. EMA 斜率    — EMA10 近 8 根斜率（方向感应）
  2. 价格位置    — 价格相对 SMA20/SMA50 位置（趋势背景）
  3. 高低点结构   — 近 20 根 HH/HL 结构（形态判断）
  4. K线主导     — 近 10 根阳线/阴线占比（动量方向）
  5. 重叠率      — 相邻 K 线高低重叠程度（趋势强度）

总分 ≥ +3 → BUY HIGH    ≥ +1 → BUY MEDIUM
总分 ≤ -3 → SELL HIGH   ≤ -1 → SELL MEDIUM
总分 = 0  → HOLD

附加: RSI 极值修正 / MACD 确认 / 量比过滤 / 支撑阻力距离

包含:
- 类: BaseStrategy — 策略抽象基类
- 类: TechnicalStrategy — 技术指标策略实现
- 函数: _decision_tree — 5 信号打分引擎
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd
import numpy as np

from app.services.agent.agent_coordinator_service import get_indicator_service

IndicatorService = get_indicator_service()


class BaseStrategy(ABC):
    """策略抽象基类。"""
    @property
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, current_position: Optional[Dict] = None, **kwargs) -> Dict: ...


class TechnicalStrategy(BaseStrategy):
    """5 信号打分制决策树策略。"""
    @property
    def name(self) -> str:
        return "TechnicalStrategy"

    def generate_signal(self, df: pd.DataFrame, current_position: Optional[Dict] = None, **kwargs) -> Dict:
        return _decision_tree(df, current_position)


# ── 信号 1: EMA 斜率 ──────────────────────────────────────

def _signal_ema_slope(df: pd.DataFrame) -> int:
    """EMA10 近 8 根斜率方向。上升 +1，下降 -1，平坦 0。"""
    if len(df) < 12:
        return 0
    ema10 = df["close"].ewm(span=10).mean()
    recent = ema10.iloc[-8:]
    slope = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100
    if slope > 0.5:
        return 1
    elif slope < -0.5:
        return -1
    return 0


# ── 信号 2: 价格位置 ──────────────────────────────────────

def _signal_price_position(df: pd.DataFrame) -> int:
    """价格相对 SMA20/SMA50 位置。在两线之上 +1，之下 -1。"""
    last = df.iloc[-1]
    price = last["close"]
    sma20 = last.get("sma_20", price)
    sma50 = last.get("sma_50", price)
    if price > sma20 and price > sma50:
        return 1
    elif price < sma20 and price < sma50:
        return -1
    return 0


# ── 信号 3: 高低点结构 ────────────────────────────────────

def _signal_hh_hl_structure(df: pd.DataFrame) -> int:
    """近 20 根 K 线的高低点结构。高点上移 +1，低点下移 -1。"""
    window = df.tail(20)
    if len(window) < 10:
        return 0
    first_half = window.iloc[:10]
    second_half = window.iloc[10:]

    hh = second_half["high"].max() > first_half["high"].max()  # higher high
    hl = second_half["low"].min() > first_half["low"].min()    # higher low
    lh = second_half["high"].max() < first_half["high"].max()  # lower high
    ll = second_half["low"].min() < first_half["low"].min()    # lower low

    if hh and hl:
        return 2  # 强趋势加 2 分
    elif hh:
        return 1
    elif lh and ll:
        return -2
    elif ll:
        return -1
    return 0


# ── 信号 4: K线主导方向 ────────────────────────────────────

def _signal_bar_dominance(df: pd.DataFrame) -> int:
    """近 10 根 K 线阳线/阴线占比。多数阳线 +1，多数阴线 -1。"""
    window = df.tail(10)
    if len(window) < 5:
        return 0
    bullish_bars = (window["close"] > window["open"]).sum()
    bearish_bars = (window["close"] < window["open"]).sum()
    ratio = bullish_bars / max(bearish_bars, 1)
    if ratio > 1.5:
        return 1
    elif ratio < 0.67:
        return -1
    return 0


# ── 信号 5: K线重叠率 ──────────────────────────────────────

def _signal_overlap_ratio(df: pd.DataFrame) -> int:
    """近 10 根相邻 K 线的高低重叠率。重叠越少趋势越强。"""
    window = df.tail(10)
    if len(window) < 5:
        return 0
    overlaps = []
    for i in range(1, len(window)):
        prev = window.iloc[i - 1]
        curr = window.iloc[i]
        overlap_range = min(prev["high"], curr["high"]) - max(prev["low"], curr["low"])
        total_range = max(prev["high"], curr["high"]) - min(prev["low"], curr["low"])
        if total_range > 0:
            overlaps.append(overlap_range / total_range)

    avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0.5
    # 重叠 < 0.3 表示趋势强，不额外加分（已由方向信号判定）
    # 重叠 > 0.6 表示震荡，返回 0
    if avg_overlap < 0.3:
        trend_up = window["close"].iloc[-1] > window["close"].iloc[0]
        return 1 if trend_up else -1
    return 0


# ── 附加: RSI 极值 ────────────────────────────────────────

def _rsi_override(rsi: float, signal: str) -> str:
    """RSI 极值时强制修正信号方向。"""
    if rsi > 75 and signal == "BUY":
        return "HOLD"
    if rsi < 25 and signal == "SELL":
        return "HOLD"
    return signal


# ── 附加: MACD 确认 ───────────────────────────────────────

def _macd_confirm(macd: float, macd_sig: float, confidence: str) -> str:
    """MACD 与信号方向一致时提升信心。"""
    if macd > macd_sig:
        return "HIGH" if confidence != "LOW" else "MEDIUM"
    elif macd < macd_sig:
        return "LOW" if confidence == "HIGH" else confidence
    return confidence


# ── 附加: 量比 ────────────────────────────────────────────

def _volume_filter(volume_ratio: float, confidence: str) -> str:
    """放量 > 1.5 提升信心，缩量 < 0.5 降低信心。"""
    if volume_ratio > 1.5:
        return confidence
    elif volume_ratio < 0.5:
        return "LOW"
    return confidence


# ── 主引擎: 汇总打分 ───────────────────────────────────────

def _decision_tree(df: pd.DataFrame, position: Optional[Dict] = None) -> Dict:
    """5 信号打分引擎，参考 PA_Agent 二元决策树设计。

    返回: {signal, confidence, reason, stop_loss, take_profit}
    """
    df = IndicatorService.calculate_all(df)
    last = df.iloc[-1]
    price = float(last["close"])
    rsi = float(last.get("rsi", 50))
    macd = float(last.get("macd", 0) or 0)
    macd_sig = float(last.get("macd_signal", 0) or 0)
    vr = float(last.get("volume_ratio", 1.0))

    # ── 打分 ──
    reasons = []
    scores = []

    s1 = _signal_ema_slope(df)
    scores.append(s1)
    if s1 != 0:
        reasons.append(f"EMA{'看涨' if s1 > 0 else '看跌'}")

    s2 = _signal_price_position(df)
    scores.append(s2)
    if s2 != 0:
        reasons.append(f"均线{'多头' if s2 > 0 else '空头'}")

    s3 = _signal_hh_hl_structure(df)
    scores.append(s3)
    if s3 >= 2:
        reasons.append("强HH/HL")
    elif s3 <= -2:
        reasons.append("强LH/LL")
    elif s3 != 0:
        reasons.append("HH" if s3 > 0 else "LL")

    s4 = _signal_bar_dominance(df)
    scores.append(s4)
    if s4 != 0:
        reasons.append(f"{'阳线' if s4 > 0 else '阴线'}主导")

    s5 = _signal_overlap_ratio(df)
    scores.append(s5)
    if s5 != 0:
        reasons.append("趋势推进")

    total = sum(scores)

    # ── 判定 ──
    if total >= 3:
        signal, confidence = "BUY", "HIGH"
    elif total >= 1:
        signal, confidence = "BUY", "MEDIUM"
    elif total <= -3:
        signal, confidence = "SELL", "HIGH"
    elif total <= -1:
        signal, confidence = "SELL", "MEDIUM"
    else:
        signal, confidence = "HOLD", "LOW"
        reasons = ["震荡整理"]

    # ── RSI 极值修正 ──
    signal = _rsi_override(rsi, signal)

    # ── MACD + 量比 信心调整 ──
    if signal != "HOLD":
        confidence = _macd_confirm(macd, macd_sig, confidence)
        confidence = _volume_filter(vr, confidence)

    # ── 止盈止损 ──
    atr_pct = IndicatorService.atr_pct(df)
    if signal == "BUY":
        stop_loss = price * (1 - max(atr_pct / 100 * 1.5, 0.015))
        take_profit = price * (1 + max(atr_pct / 100 * 3, 0.03))
    elif signal == "SELL":
        stop_loss = price * (1 + max(atr_pct / 100 * 1.5, 0.015))
        take_profit = price * (1 - max(atr_pct / 100 * 3, 0.03))
    else:
        stop_loss = price * 0.98
        take_profit = price * 1.02

    reason = " + ".join(reasons) if reasons else "趋势不明朗"

    return {
        "signal": signal,
        "confidence": confidence,
        "reason": f"得分{total:+d}: {reason}",
        "stop_loss": float(round(stop_loss, 2)),
        "take_profit": float(round(take_profit, 2)),
    }
