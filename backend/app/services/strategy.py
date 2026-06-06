"""策略协调服务 — 管理多个策略，并行执行，加权汇总"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from app.strategies.base import BaseStrategy


@dataclass
class AggregatedSignal:
    symbol: str
    signal: str
    confidence: str
    reason: str
    stop_loss: float
    take_profit: float
    source_count: int
    strategy_signals: List[dict] = field(default_factory=list)


class StrategyService:
    """策略协调服务

    管理多个策略实例，在每个 tick 周期并行调用它们生成信号，
    然后按加权投票汇总为一个最终信号。
    """

    def __init__(self, strategies: List[BaseStrategy], default_weight: float = 1.0):
        self._strategies = strategies
        self._weights: Dict[str, float] = {s.name: default_weight for s in strategies}
        self._win_rates: Dict[str, float] = {s.name: 0.5 for s in strategies}

    @property
    def strategy_names(self) -> List[str]:
        return [s.name for s in self._strategies]

    async def analyze(
        self, df: pd.DataFrame, position: dict | None = None
    ) -> AggregatedSignal:
        """并行调用所有策略并汇总信号"""
        symbol = "BTC/USDT:USDT"

        async def _run_one(s: BaseStrategy) -> dict:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, s.generate_signal, df, position
            )

        results = await asyncio.gather(
            *[_run_one(s) for s in self._strategies], return_exceptions=True
        )

        signals = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            result["_strategy"] = self._strategies[i].name
            signals.append(result)

        if not signals:
            return AggregatedSignal(
                symbol=symbol,
                signal="HOLD",
                confidence="LOW",
                reason="所有策略均失败",
                stop_loss=0,
                take_profit=0,
                source_count=0,
            )

        # 加权投票
        return self._weighted_vote(symbol, signals)

    def _weighted_vote(self, symbol: str, signals: List[dict]) -> AggregatedSignal:
        weights = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        for s in signals:
            w = self._weights.get(s["_strategy"], 1.0)
            conf_map = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
            weight = w * conf_map.get(s.get("confidence", "MEDIUM"), 0.3)
            weights[s["signal"]] += weight

        winner = max(weights, key=weights.get)
        # 找理由（取权重最高的那个策略的理由）
        best = max(signals, key=lambda s: self._weights.get(s["_strategy"], 1.0))

        return AggregatedSignal(
            symbol=symbol,
            signal=winner,
            confidence="HIGH" if weights[winner] > sum(weights.values()) * 0.6 else "MEDIUM",
            reason=best.get("reason", f"加权投票: {winner}"),
            stop_loss=best.get("stop_loss", 0),
            take_profit=best.get("take_profit", 0),
            source_count=len(signals),
            strategy_signals=signals,
        )

    def update_weight(self, strategy_name: str, weight: float) -> None:
        self._weights[strategy_name] = weight

    async def get_status(self) -> List[dict]:
        return [
            {
                "name": s.name,
                "weight": self._weights.get(s.name, 1.0),
            }
            for s in self._strategies
        ]
