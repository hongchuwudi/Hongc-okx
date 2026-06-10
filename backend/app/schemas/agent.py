"""
创建时间: 2026-06-06
作者: hongchuwudi
描述: Agent 内部数据结构 — props（非 API 请求/响应）
"""

from dataclasses import dataclass
from enum import Enum


class Signal(str, Enum):
    """交易信号"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Confidence(str, Enum):
    """信号置信度"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class AgentReport:
    """单个 Agent 的决策报告"""
    reasoning: str = ""
    signal: Signal = Signal.HOLD
    confidence: Confidence = Confidence.MEDIUM
    sl: float = 0.0
    tp: float = 0.0
    position_pct: float = 0.0
