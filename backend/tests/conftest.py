"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: conftest.py 测试夹具
描述: 全局测试夹具 — 模拟 OHLCV 数据、持仓、账户

包含:
- 函数: sample_df — 200 行模拟 K 线
- 函数: sample_position — 模拟多头持仓
- 函数: load_fixtures — 将测试数据注入 toolkits.toolkit_data
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """200 行模拟 OHLCV 数据，含上升趋势。"""
    np.random.seed(42)
    n = 200
    close = np.cumsum(np.random.randn(n) * 50) + 95000
    return pd.DataFrame({
        "close": close,
        "high": close + np.random.rand(n) * 200,
        "low": close - np.random.rand(n) * 200,
        "volume": np.random.rand(n) * 1000 + 500,
    }, index=pd.date_range("2026-06-01", periods=n, freq="1min"))


@pytest.fixture
def sample_position():
    """模拟 BTC/USDT 多头持仓。"""
    return {"side": "long", "size": 0.1, "entry_price": 94000, "unrealized_pnl": 200, "leverage": 1}


@pytest.fixture
def load_fixtures(sample_df, sample_position):
    """将模拟数据注入 toolkits.toolkit_data 缓存。"""
    from app.agents.toolkits.toolkit_data import load_data
    load_data(sample_df, price=95000.0, equity=10000.0, position=sample_position)
