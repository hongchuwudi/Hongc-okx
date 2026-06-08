"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: 策略 schema — /api/strategies
"""

from pydantic import BaseModel


class StrategyItem(BaseModel):
    name: str
    type: str
    description: str
    timeframe: str


class StrategyListResponse(BaseModel):
    strategies: list[StrategyItem]
