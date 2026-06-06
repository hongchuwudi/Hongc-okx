"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: base.py 中文名
描述: 策略抽象基类 — 定义所有交易策略必须实现的接口

包含:
- 类: BaseStrategy — 策略抽象基类，定义信号生成接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd


class BaseStrategy(ABC):
    """所有交易策略必须实现的抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称（只读属性）"""
        ...

    @abstractmethod
    def generate_signal(
        self,
        df: pd.DataFrame,
        current_position: Optional[Dict] = None,
        **kwargs,
    ) -> Dict:
        """
        根据 OHLCV 数据生成交易信号。

        Returns:
            {
                "signal": "BUY" | "SELL" | "HOLD",
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reason": str,
                "stop_loss": float,
                "take_profit": float,
            }
        """
        ...
