"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: strategy.py 中文名
描述: 策略协调服务 — 管理多个策略，并行执行信号生成并加权汇总

包含:
- 类: AggregatedSignal — 多策略汇总后的最终信号数据类
- 类: StrategyService — 策略协调服务，并行执行并加权投票
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from app.strategies.base import BaseStrategy


@dataclass
class AggregatedSignal:
    """多策略加权汇总后的最终交易信号"""
    symbol: str                    # 交易对
    signal: str                    # 最终信号 BUY/SELL/HOLD
    confidence: str                # 信心水平 HIGH/MEDIUM/LOW
    reason: str                    # 决策理由
    stop_loss: float               # 止损价格
    take_profit: float             # 止盈价格
    source_count: int              # 参与投票的策略数
    strategy_signals: List[dict] = field(default_factory=list)  # 各策略原始信号


class StrategyService:
    """策略协调服务

    管理多个策略实例，在每个 tick 周期并行调用它们生成信号，
    然后按加权投票汇总为一个最终信号。
    """

    def __init__(self, strategies: List[BaseStrategy], default_weight: float = 1.0):
        # 策略实例列表
        self._strategies = strategies
        # 各策略权重（用于加权投票）
        self._weights: Dict[str, float] = {s.name: default_weight for s in strategies}
        # 各策略胜率记录
        self._win_rates: Dict[str, float] = {s.name: 0.5 for s in strategies}

    @property
    def strategy_names(self) -> List[str]:
        """获取所有策略名称列表"""
        return [s.name for s in self._strategies]

    async def analyze(
        self, df: pd.DataFrame, position: dict | None = None
    ) -> AggregatedSignal:
        """并行调用所有策略生成信号，然后加权汇总"""
        symbol = "BTC/USDT:USDT"

        # 在线程池中同步执行每个策略的 generate_signal
        async def _run_one(s: BaseStrategy) -> dict:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, s.generate_signal, df, position
            )

        # 并行执行所有策略
        results = await asyncio.gather(
            *[_run_one(s) for s in self._strategies], return_exceptions=True
        )

        signals = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            result["_strategy"] = self._strategies[i].name
            signals.append(result)

        # 所有策略均失败时返回 HOLD
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

        # 加权投票决定最终信号
        return self._weighted_vote(symbol, signals)

    def _weighted_vote(self, symbol: str, signals: List[dict]) -> AggregatedSignal:
        """根据策略权重和信心水平加权投票，选出最终信号"""
        weights = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        for s in signals:
            w = self._weights.get(s["_strategy"], 1.0)
            conf_map = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
            weight = w * conf_map.get(s.get("confidence", "MEDIUM"), 0.3)
            weights[s["signal"]] += weight

        winner = max(weights, key=weights.get)
        # 取权重最高的策略的理由作为最终理由
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
        """更新指定策略的权重"""
        self._weights[strategy_name] = weight

    async def get_status(self) -> List[dict]:
        """获取各策略的运行状态"""
        return [
            {
                "name": s.name,
                "weight": self._weights.get(s.name, 1.0),
            }
            for s in self._strategies
        ]
