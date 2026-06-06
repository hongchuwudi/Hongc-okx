"""策略抽象基类"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd


class BaseStrategy(ABC):
    """所有交易策略必须实现的接口"""

    @property
    @abstractmethod
    def name(self) -> str:
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
