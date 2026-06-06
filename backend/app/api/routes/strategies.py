"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: strategies.py 策略列表API路由
描述: 策略管理 API — 返回系统支持的策略列表

包含:
- 函数: get_strategies — 获取当前启用的策略列表（静态配置）
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/strategies")
def get_strategies():
    """返回当前启用的策略列表（静态配置，后续可扩展为动态加载）"""
    return {
        "strategies": [
            {
                "name": "DeepSeekStrategy",
                "type": "ai",
                "description": "基于 DeepSeek 大模型的 AI 交易策略",
                "timeframe": "1h",
            },
            {
                "name": "TechnicalStrategy",
                "type": "technical",
                "description": "基于 SMA + RSI + MACD 的技术指标策略",
                "timeframe": "1h",
            },
        ]
    }
