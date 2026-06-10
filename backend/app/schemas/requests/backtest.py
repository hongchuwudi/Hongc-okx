"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: backtest.py 回测请求模型
描述: 回测 API 的请求参数校验模型
"""

from pydantic import BaseModel


# 回测请求参数 — 策略类型、交易品种、时间周期、初始资金、仓位比例、费率、预热、K线数量、AI激进程度
class RunRequest(BaseModel):
    # 策略类型，如 technical, momentum
    strategy: str = "technical"
    # 交易品种，如 BTC/USDT:USDT
    symbol: str = "BTC/USDT:USDT"
    # 时间周期，如 1m, 5m, 1h
    timeframe: str = "1h"
    # 初始资金 (USDT)
    initial_capital: float = 100.0
    # 仓位比例，如 0.5 表示 50% 资金用于开仓
    position_ratio: float = 0.5
    # 手续费率，如 0.001 表示 0.1%
    fee_rate: float = 0.001
    # 预热期（最少K线数量，用于计算技术指标）
    warmup: int = 50
    # K线数据条数
    data_limit: int = 500
    # AI 模型温度参数，控制输出随机性 (0~1)
    temperature: float = 0.1