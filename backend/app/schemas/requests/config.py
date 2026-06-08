"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: config.py 配置请求模型
描述: 配置 API 的请求参数校验模型
"""

from pydantic import BaseModel


# 前端提交的配置更新 — 所有字段可选，只更新传入的字段
class ConfigUpdate(BaseModel):
    # 交易品种，如 BTC/USDT:USDT
    symbol: str | None = None
    # 杠杆倍数，如 10
    leverage: int | None = None
    # 时间周期，如 1m, 5m, 1h
    timeframe: str | None = None
    # K线数据点数
    data_points: int | None = None
    # Tick 间隔秒数
    tick_interval_seconds: int | None = None
    # 单次下单金额 (USDT)
    order_amount: float | None = None
    # 最大仓位比例，如 0.8 表示 80%
    max_position_ratio: float | None = None
    # 日内最大回撤百分比
    max_daily_drawdown_pct: float | None = None
    # 日内最大亏损金额 (USDT)
    max_daily_loss_usdt: float | None = None
    # Agent 运行模式，如 single, voting
    agent_mode: str | None = None
    # 是否模拟盘，True 为模拟交易
    sandbox: bool | None = None