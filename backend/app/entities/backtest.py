"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: backtest.py 中文名
描述: 回测 ORM 模型 — 存储回测运行记录和结果

包含:
- 类: BacktestRun — 回测运行记录，包含参数、指标和结果数据
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.entities import Base


# 回测运行记录 — 存储每次回测的参数、性能指标和结果
class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 策略名称
    strategy_name = Column(String(50))
    # 交易对
    symbol = Column(String(20))
    # 时间周期
    timeframe = Column(String(10))
    # 初始资金
    initial_capital = Column(Float)
    # 仓位比例
    position_ratio = Column(Float)
    # 手续费率
    fee_rate = Column(Float)
    # 数据条数
    data_count = Column(Integer)
    # 预热期（用于计算指标）
    warmup = Column(Integer)
    # 回测状态: running / completed / failed
    status = Column(String(20), default="running")
    # 最终权益
    final_equity = Column(Float, nullable=True)
    # 总收益率（%）
    total_return_pct = Column(Float, nullable=True)
    # 胜率（%）
    win_rate = Column(Float, nullable=True)
    # 盈亏比
    profit_factor = Column(Float, nullable=True)
    # 最大回撤（%）
    max_drawdown_pct = Column(Float, nullable=True)
    # 夏普比率
    sharpe_ratio = Column(Float, nullable=True)
    # 总交易次数
    total_trades = Column(Integer, nullable=True)
    # 盈利次数
    winning_trades = Column(Integer, nullable=True)
    # 亏损次数
    losing_trades = Column(Integer, nullable=True)
    # 平均交易盈亏
    avg_trade_pnl = Column(Float, nullable=True)
    # 配置 JSON
    config_json = Column(Text, nullable=True)
    # 指标 JSON
    metrics_json = Column(Text, nullable=True)
    # 交易记录 JSON
    trades_json = Column(Text, nullable=True)
    # 权益曲线 JSON
    equity_json = Column(Text, nullable=True)
    # 错误信息
    error_message = Column(Text, nullable=True)
    # 开始时间
    started_at = Column(DateTime, default=datetime.utcnow)
    # 完成时间
    finished_at = Column(DateTime, nullable=True)
