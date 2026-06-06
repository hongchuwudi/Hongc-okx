"""策略管理 API — /api/strategies"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/strategies")
def get_strategies():
    """返回当前启用的策略列表（静态配置，后续可扩展为动态）"""
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
