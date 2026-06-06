"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: base.py Server基类
描述: Server 基类 — 管理 OHLCV DataFrame 加载，所有工具函数从此获取行情数据

包含:
- 函数: load_data — coordinator 启动时调用，注入数据
- 函数: _df — 获取价格 DataFrame
- 函数: _price/_equity/_position — 获取当前快照数据
"""

import pandas as pd

_data: dict = {}

def load_data(df: pd.DataFrame, price: float, equity: float, position: dict | None = None):
    """每 tick 由 coordinator 调用，注入 OHLCV 和账户数据。"""
    _data["df"] = df
    _data["price"] = price
    _data["equity"] = equity
    _data["position"] = position or {}

def _df() -> pd.DataFrame:
    return _data.get("df", pd.DataFrame())


def _price() -> float:
    return _data.get("price", 0.0)


def _equity() -> float:
    return _data.get("equity", 0.0)


def _position() -> dict:
    return _data.get("position", {})
