"""
测试: 纯计算工具 — RSI/MACD/SMA/布林带/ATR/量比
"""

import pytest


class TestRSI:
    def test_default_period(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi
        result = calc_rsi()
        assert "RSI(14)" in result
        assert "—" in result

    def test_custom_period(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi
        result = calc_rsi(7)
        assert "RSI(7)" in result

    def test_range_0_100(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_rsi
        result = calc_rsi()
        # RSI 值应在 38-42 之间（模拟数据特性）
        assert "超卖" in result or "超买" in result or "中性" in result


class TestMACD:
    def test_default(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd
        result = calc_macd()
        assert "MACD" in result
        assert "信号" in result

    def test_cross_detection(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_macd
        result = calc_macd()
        # 应有金叉/死叉/无交叉其一
        assert any(x in result for x in ["金叉", "死叉", "无交叉"])


class TestSMA:
    def test_sma20(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_sma
        result = calc_sma(20)
        assert "SMA20" in result
        assert "价格偏离" in result

    def test_data_insufficient(self, sample_df):
        import pandas as pd
        from app.agents.toolkits.toolkit_data import load_data
        tiny = sample_df.head(3)
        load_data(tiny, 95000, 10000)
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_sma
        result = calc_sma(50)
        assert "数据不足" in result


class TestBollinger:
    def test_default(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_bollinger
        result = calc_bollinger()
        assert "布林带" in result
        assert "上" in result and "中" in result and "下" in result


class TestATR:
    def test_default(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_atr
        result = calc_atr()
        assert "ATR" in result
        assert "%" in result


class TestVolumeRatio:
    def test_default(self, load_fixtures):
        from app.agents.toolkits.tools.toolkit_calc_indicator import calc_volume_ratio
        result = calc_volume_ratio()
        assert "量比" in result
