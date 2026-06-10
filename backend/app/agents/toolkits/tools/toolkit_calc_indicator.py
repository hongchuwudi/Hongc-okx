"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: indicators.py 技术指标计算
描述: 纯 pandas/numpy 计算函数 — RSI、MACD、SMA、布林带、ATR。不依赖任何框架

包含:
- calc_rsi — Wilder 平滑 RSI
- calc_macd — MACD 线/信号线/柱状图
- calc_sma — 简单移动平均
- calc_bollinger — 布林带上中下轨
- calc_atr — 平均真实波幅
- calc_volume_ratio — 量比
- calc_trend — 趋势方向判断
- get_price — 当前价格
"""

import numpy as np
import pandas as pd

from app.agents.toolkits.toolkit_data import _df, _price


def get_price() -> str:
    """获取当前价格。"""
    return f"当前价格: ${_price():,.2f}"


def calc_rsi(period: int = 14) -> str:
    """Wilder 平滑 RSI。"""
    df = _df()
    if df.empty or "close" not in df.columns: return "RSI: 无数据"
    delta = df["close"].diff()
    gain = delta.clip(lower=0); loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = (100 - 100 / (1 + rs)).iloc[-1]
    label = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")
    return f"RSI({period}): {rsi:.1f} — {label}"


def calc_macd(fast: int = 12, slow: int = 26, signal: int = 9) -> str:
    """MACD 指标。"""
    df = _df()
    if df.empty or "close" not in df.columns: return "MACD: 无数据"
    ema_f = df["close"].ewm(span=fast, adjust=False).mean()
    ema_s = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_f - ema_s
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    hv, sv, ph = hist.iloc[-1], signal_line.iloc[-1], (hist.iloc[-2] if len(hist) > 1 else 0)
    cross = "金叉 ↑" if (ph < 0 < hv) else ("死叉 ↓" if (ph > 0 > hv) else "无交叉")
    d = "扩大" if abs(hv) > abs(ph) else "收缩"
    return f"MACD: {macd_line.iloc[-1]:.2f} | 信号: {sv:.2f} | 柱: {hv:.2f}({d}) | {cross}"


def calc_sma(period: int) -> str:
    """简单移动平均。"""
    df = _df(); price = _price()
    if df.empty or "close" not in df.columns: return f"SMA{period}: 无数据"
    sma = df["close"].rolling(period).mean().iloc[-1]
    if pd.isna(sma) or sma == 0: return f"SMA{period}: 数据不足"
    return f"SMA{period}: {sma:.1f} (价格偏离{(price - sma) / sma * 100:+.2f}%)"


def calc_bollinger(period: int = 20, std_dev: float = 2.0) -> str:
    """布林带。"""
    df = _df(); price = _price()
    if df.empty or "close" not in df.columns: return "布林带: 无数据"
    sma = df["close"].rolling(period).mean().iloc[-1]
    std = df["close"].rolling(period).std().iloc[-1]
    upper, lower = sma + std_dev * std, sma - std_dev * std
    br = upper - lower; pos = (price - lower) / br if br > 0 else 0.5
    w = (upper - lower) / sma * 100 if sma > 0 else 0
    return f"布林带: 上{upper:.0f} 中{sma:.0f} 下{lower:.0f} | 价格位置:{pos:.1%} (带宽{w:.1f}%)"


def calc_atr(period: int = 14) -> str:
    """平均真实波幅。"""
    df = _df(); price = _price()
    if df.empty or "close" not in df.columns: return "ATR: 无数据"
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
    atr_v = tr.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    return f"ATR: {atr_v:.1f} ({atr_v / price * 100:.2f}%)" if price > 0 else f"ATR: {atr_v:.1f}"


def calc_volume_ratio(period: int = 20) -> str:
    """量比。"""
    df = _df()
    if df.empty or "volume" not in df.columns: return "量比: 无数据"
    avg = df["volume"].rolling(period).mean().iloc[-1]
    r = df["volume"].iloc[-1] / avg if avg > 0 else 1
    l = "异常放量" if r > 2 else ("异常缩量" if r < 0.5 else "正常")
    return f"量比: {r:.2f} — {l}"


def calc_trend() -> str:
    """趋势综合分析。"""
    df = _df(); price = _price()
    if df.empty or "close" not in df.columns: return "趋势: 无数据"
    smas = [df["close"].rolling(p).mean().iloc[-1] for p in (5, 20, 50)]; s5, s20, s50 = smas
    short = "bullish" if price > s5 else ("bearish" if price < s5 else "neutral")
    med = "bullish" if s5 > s20 > s50 else ("bearish" if s5 < s20 < s50 else "neutral")
    overall = short if short == med else "震荡/分歧"
    return f"趋势 短期:{short} | 中期:{med} | 整体:{overall}"
