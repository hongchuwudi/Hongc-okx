"""
策略抽象基类 — 所有交易策略必须实现 generate_signal()
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd


class BaseStrategy(ABC):
    """策略基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
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

        Args:
            df: 原始 OHLCV DataFrame，列: [timestamp, open, high, low, close, volume]
            current_position: 当前持仓 {side, size, entry_price, unrealized_pnl} 或 None
            **kwargs: 扩展参数 (exchange, account_info, sentiment_data 等)

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
