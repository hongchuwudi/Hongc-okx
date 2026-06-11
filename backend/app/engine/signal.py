"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: Signal — 交易信号数据类，单次 tick 的完整决策信息
"""

from dataclasses import dataclass, field


@dataclass
class Signal:
    """单次 tick 的交易信号，包含方向、置信度、止盈止损等完整决策。"""
    signal: str = "HOLD"               # BUY / SELL / HOLD
    confidence: str = "MEDIUM"         # HIGH / MEDIUM / LOW
    reason: str = ""                   # 决策理由
    stop_loss: float = 0.0             # 止损价
    take_profit: float = 0.0           # 止盈价
    source_count: int = 0              # 参与决策的代理数量
    agent_reports: dict = field(default_factory=dict)  # {agent_name: report}
