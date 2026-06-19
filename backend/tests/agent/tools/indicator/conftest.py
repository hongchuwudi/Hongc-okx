"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: conftest.py indicator 测试共享夹具
描述: 加载项目真实 K 线数据 + 构造边界场景数据，注入 toolkit_data 缓存

数据来源:
- 真实行情: data/kline/demo/doge/doge_1m_*.csv (2000 行, DOGE/USDT 1m)
- 边界场景: 构造确定性 DataFrame (纯涨/纯跌/横盘/固定TR/恒定成交量)

包含:
- fixture: real_kline — 加载真实 DOGE 1m K 线并注入缓存
- fixture: uptrend_df — 30 天纯涨 close 100→129
- fixture: downtrend_df — 30 天纯跌 close 129→100
- fixture: sideways_df — 30 天横盘 close 恒为 100
- fixture: fixed_tr_df — 30 天 TR 恒为 2.0
- fixture: constant_vol_df — 30 天 volume 恒为 1000
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# 真实 K 线数据目录 (相对于 backend/)
# conftest.py → indicator → tools → agent → tests → backend → data/kline/demo/doge
_KLINE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "kline" / "demo" / "doge"


@pytest.fixture(scope="module")
def real_kline():
    """加载真实 DOGE 1m K 线 (2000 行)，注入 toolkit_data 缓存。"""
    csv_files = sorted(_KLINE_DIR.glob("doge_1m_*.csv"))
    assert csv_files, f"未找到 DOGE 1m K 线文件: {_KLINE_DIR}"

    df = pd.read_csv(csv_files[0])
    # 统一列名为小写
    df.columns = [c.lower() for c in df.columns]
    assert {"open", "high", "low", "close", "volume"}.issubset(set(df.columns)), \
        f"K 线列名不符合预期: {df.columns.tolist()}"

    from app.agents.toolkits.toolkit_data import load_data
    price = float(df["close"].iloc[-1])
    load_data(df, price=price, equity=10000.0, position={
        "side": "long", "size": 100.0, "entry_price": float(df["close"].iloc[-100]),
        "unrealized_pnl": 5.0, "leverage": 10,
    })
    return df


@pytest.fixture(scope="module")
def uptrend_df():
    """30 天纯涨: close 100→129 (每天+1), high=close+1, low=close-1, volume=1000"""
    n = 30
    close = np.arange(100, 100 + n, dtype=float)
    df = pd.DataFrame({
        "close": close, "high": close + 1.0, "low": close - 1.0,
        "volume": np.full(n, 1000.0),
    })
    from app.agents.toolkits.toolkit_data import load_data
    load_data(df, price=129.0, equity=10000.0)
    return df


@pytest.fixture(scope="module")
def downtrend_df():
    """30 天纯跌: close 129→100 (每天-1)"""
    n = 30
    close = np.arange(129, 99, -1, dtype=float)
    df = pd.DataFrame({
        "close": close, "high": close + 1.0, "low": close - 1.0,
        "volume": np.full(n, 1000.0),
    })
    from app.agents.toolkits.toolkit_data import load_data
    load_data(df, price=100.0, equity=10000.0)
    return df


@pytest.fixture(scope="module")
def sideways_df():
    """30 天横盘: close 恒为 100 (±0.01 噪声避免除零)"""
    n = 30
    np.random.seed(1)
    close = np.full(n, 100.0) + np.random.randn(n) * 0.01
    df = pd.DataFrame({
        "close": close, "high": close + 0.5, "low": close - 0.5,
        "volume": np.full(n, 1000.0),
    })
    from app.agents.toolkits.toolkit_data import load_data
    load_data(df, price=100.0, equity=10000.0)
    return df


@pytest.fixture(scope="module")
def fixed_tr_df():
    """30 天 TR 恒为 2.0: high=close+1, low=close-1, close 每天+1"""
    n = 30
    close = np.arange(100, 100 + n, dtype=float)
    df = pd.DataFrame({
        "close": close, "high": close + 1.0, "low": close - 1.0,
        "volume": np.full(n, 1000.0),
    })
    from app.agents.toolkits.toolkit_data import load_data
    load_data(df, price=129.0, equity=10000.0)
    return df


@pytest.fixture(scope="module")
def constant_vol_df():
    """30 天恒定成交量 1000，close 每天+1"""
    n = 30
    close = np.arange(100, 100 + n, dtype=float)
    df = pd.DataFrame({
        "close": close, "high": close + 1.0, "low": close - 1.0,
        "volume": np.full(n, 1000.0),
    })
    from app.agents.toolkits.toolkit_data import load_data
    load_data(df, price=129.0, equity=10000.0)
    return df


@pytest.fixture(scope="module")
def empty_df():
    """空 DataFrame"""
    from app.agents.toolkits.toolkit_data import load_data
    load_data(pd.DataFrame(), 0.0, 0.0)
    return pd.DataFrame()
