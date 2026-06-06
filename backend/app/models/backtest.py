"""回测 ORM 模型"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from app.models import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(50))
    symbol = Column(String(20))
    timeframe = Column(String(10))
    initial_capital = Column(Float)
    position_ratio = Column(Float)
    fee_rate = Column(Float)
    data_count = Column(Integer)
    warmup = Column(Integer)
    status = Column(String(20), default="running")  # running / completed / failed
    final_equity = Column(Float, nullable=True)
    total_return_pct = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)
    avg_trade_pnl = Column(Float, nullable=True)
    config_json = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True)
    trades_json = Column(Text, nullable=True)
    equity_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
