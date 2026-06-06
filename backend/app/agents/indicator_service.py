"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: indicator_service.py 统一技术指标计算服务
描述: 统一技术指标服务 — 全项目唯一指标计算来源

包含:
- 类: IndicatorService — 静态方法集合，提供技术指标计算、趋势分析、支撑阻力、市场状态分类
- 函数: calculate_all — 对 OHLCV DataFrame 计算全部技术指标
- 函数: latest_indicators — 返回最后一根 K 线的指标快照字典
- 函数: atr_pct — 计算 ATR 占当前价格的百分比
- 函数: calc_rsi — 计算简易 RSI 值
- 函数: trend_analysis — 趋势分析（短期/中期/整体）
- 函数: support_resistance — 静态 + 动态支撑阻力计算
- 函数: market_state — 综合市场状态分类
"""

import pandas as pd


class IndicatorService:
    """静态方法集合，所有策略和 Agent 统一调用此处计算。"""

    # ── 完整指标 DataFrame ──────────────────────────────────

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """对 OHLCV DataFrame 计算全部技术指标，返回增强后的 DataFrame。"""
        df = df.copy()
        # 移动平均线
        df["sma_5"] = df["close"].rolling(window=5, min_periods=1).mean()
        df["sma_20"] = df["close"].rolling(window=20, min_periods=1).mean()
        df["sma_50"] = df["close"].rolling(window=50, min_periods=1).mean()
        # 指数移动平均（用于 MACD）
        df["ema_12"] = df["close"].ewm(span=12).mean()
        df["ema_26"] = df["close"].ewm(span=26).mean()
        # MACD 指标
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        # RSI 指标
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

        # 布林带
        df["bb_middle"] = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-10)

        # 成交量指标
        df["volume_ma"] = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma"].replace(0, 1)

        # 填充前后缺失值
        df = df.bfill().ffill()
        return df

    # ── 单值查询 ─────────────────────────────────────────────

    @staticmethod
    def latest_indicators(df: pd.DataFrame) -> dict:
        """返回最后一根 K 线的指标快照字典。"""
        row = df.iloc[-1]
        return {
            "sma_5": float(row.get("sma_5", 0) or 0),  # 5 期 SMA
            "sma_20": float(row.get("sma_20", 0) or 0),  # 20 期 SMA
            "sma_50": float(row.get("sma_50", 0) or 0),  # 50 期 SMA
            "rsi": float(row.get("rsi", 0) or 0),  # RSI 值
            "macd": float(row.get("macd", 0) or 0),  # MACD 线
            "macd_signal": float(row.get("macd_signal", 0) or 0),  # MACD 信号线
            "macd_histogram": float(row.get("macd_histogram", 0) or 0),  # MACD 柱状图
            "bb_upper": float(row.get("bb_upper", 0) or 0),  # 布林上轨
            "bb_lower": float(row.get("bb_lower", 0) or 0),  # 布林下轨
            "bb_position": float(row.get("bb_position", 0) or 0),  # 价格在布林带中的位置
            "volume_ratio": float(row.get("volume_ratio", 0) or 0),  # 量比
        }

    @staticmethod
    def atr_pct(df: pd.DataFrame, period: int = 14) -> float:
        """ATR 占当前价格的百分比。"""
        # 计算真实波幅 TR
        tr = pd.concat([
            df["high"] - df["low"],  # 当日最高-最低
            (df["high"] - df["close"].shift()).abs(),  # 当日最高-前日收盘
            (df["low"] - df["close"].shift()).abs(),  # 当日最低-前日收盘
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]  # ATR = TR 的周期均值
        price = df["close"].iloc[-1]
        return float((atr / price) * 100) if price > 0 else 2.0

    @staticmethod
    def calc_rsi(df: pd.DataFrame, period: int = 14) -> float:
        """简易 RSI 值。"""
        try:
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0.0).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
            rs = gain / loss
            return float(100.0 - (100.0 / (1.0 + rs.iloc[-1])))
        except Exception:
            return 50.0  # 计算失败返回中性值

    # ── 趋势分析 ─────────────────────────────────────────────

    @staticmethod
    def trend_analysis(df: pd.DataFrame) -> dict:
        """返回趋势分析字典（兼容现有使用方）。"""
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
                "short_term": short,  # 短期趋势（vs SMA20）
                "medium_term": medium,  # 中期趋势（vs SMA50）
                "macd": macd_dir,  # MACD 方向
                "overall": overall,  # 整体趋势判断
                "rsi_level": float(last.get("rsi", 50)),  # RSI 水平
            }
        except Exception:
            return {"short_term": "N/A", "medium_term": "N/A", "macd": "N/A", "overall": "N/A", "rsi_level": 50}

    # ── 支撑阻力 ─────────────────────────────────────────────

    @staticmethod
    def support_resistance(df: pd.DataFrame, lookback: int = 20) -> dict:
        """静态 + 动态（布林带）支撑阻力。"""
        try:
            recent_high = float(df["high"].tail(lookback).max())  # 近期最高价（静态阻力）
            recent_low = float(df["low"].tail(lookback).min())  # 近期最低价（静态支撑）
            price = float(df["close"].iloc[-1])
            bb_upper = float(df["bb_upper"].iloc[-1])  # 布林上轨（动态阻力）
            bb_lower = float(df["bb_lower"].iloc[-1])  # 布林下轨（动态支撑）
            return {
                "static_resistance": recent_high,
                "static_support": recent_low,
                "dynamic_resistance": bb_upper,
                "dynamic_support": bb_lower,
                "price_vs_resistance": ((recent_high - price) / price) * 100,  # 距阻力的百分比
                "price_vs_support": ((price - recent_low) / recent_low) * 100,  # 距支撑的百分比
            }
        except Exception:
            return {}

    # ── 市场状态 ─────────────────────────────────────────────

    @staticmethod
    def market_state(df: pd.DataFrame) -> dict:
        """综合市场状态分类（趋势 + 波动率）。"""
        try:
            last = df.iloc[-1]
            price = float(last["close"])
            sma_5 = float(last.get("sma_5", 0) or 0)
            sma_20 = float(last.get("sma_20", 0) or 0)
            sma_50 = float(last.get("sma_50", 0) or 0)
            atr = IndicatorService.atr_pct(df)

            # 通过均线排列判断趋势强度
            if sma_5 > sma_20 > sma_50:
                ts, conf = "强上涨", 0.9
            elif sma_5 < sma_20 < sma_50:
                ts, conf = "强下跌", 0.9
            elif sma_20 > 0 and abs(sma_5 - sma_20) / sma_20 < 0.005:
                ts, conf = "震荡", 0.7
            else:
                ts, conf = "弱趋势", 0.5

            # 结合波动率分类
            if atr > 3:
                state = f"高波动{ts}"
            elif atr < 1:
                state = "低波动震荡"
            else:
                state = ts

            return {"state": state, "confidence": conf, "atr_pct": atr, "trend_strength": ts}
        except Exception:
            return {"state": "未知", "confidence": 0.5, "atr_pct": 2.0, "trend_strength": "未知"}
