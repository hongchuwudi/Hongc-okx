"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: strategies.py 策略列表API路由
描述: 策略管理 API — 返回系统支持的策略列表

包含:
- 端点: GET /api/strategies — 返回当前启用的策略列表（名称/类型/描述/周期）
"""

from fastapi import APIRouter

from app.services.trading.strategy import StrategyService
from app.schemas.responses.strategy import StrategyListResponse

router = APIRouter(prefix="/api/v1")


# 策略列表 — 返回系统当前支持的所有交易策略，含 AI 深度策略和技术指标策略
@router.get("/strategies", response_model=StrategyListResponse)
def get_strategies():
    return StrategyService.get_strategy_list()
