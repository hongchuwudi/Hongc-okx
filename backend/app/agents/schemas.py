"""Pydantic 数据模型 — 多 Agent 系统的类型定义"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AgentRole(str, Enum):
    MARKET = "market"
    RISK = "risk"
    MEMORY = "memory"


class AgentReport(BaseModel):
    """单个 Agent 的分析输出"""

    signal: Signal = Signal.HOLD
    confidence: Confidence = Confidence.LOW
    reasoning: str = Field(default="", max_length=300)
    sl: float = 0.0
    tp: float = 0.0
    position_pct: float = Field(default=0.0, ge=0, le=100)


class TradeDecision(BaseModel):
    """最终聚合决策 — 与前端 API 兼容"""

    signal: Signal = Signal.HOLD
    confidence: Confidence = Confidence.LOW
    reason: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_pct: float = 0.0
    source_count: int = 0
    agent_reports: dict = Field(default_factory=dict)
