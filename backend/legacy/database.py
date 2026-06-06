"""
SQLite 数据库模块 — SQLAlchemy ORM 模型 + CRUD 辅助函数
"""
import os
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, Integer, Float, String, Text, DateTime, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DB_PATH = os.getenv("DB_PATH", "trading_bot.db")
_engine = None
_SessionLocal = None

Base = declarative_base()


# ── ORM Models ──────────────────────────────────────────────

class SystemStatus(Base):
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, default=1)  # 单行 (id=1)
    status = Column(String(20), default="stopped")
    last_update = Column(DateTime)
    balance = Column(Float, default=0)
    equity = Column(Float, default=0)
    leverage = Column(Integer, default=1)
    btc_price = Column(Float, default=0)
    btc_change = Column(Float, default=0)
    timeframe = Column(String(10), default="1h")
    mode = Column(String(30), default="cross-oneway")
    position_side = Column(String(10), nullable=True)
    position_size = Column(Float, default=0)
    position_entry_price = Column(Float, default=0)
    position_unrealized_pnl = Column(Float, default=0)
    ai_signal = Column(String(10), default="HOLD")
    ai_confidence = Column(String(10), default="N/A")
    ai_reason = Column(Text, default="")
    ai_stop_loss = Column(Float, default=0)
    ai_take_profit = Column(Float, default=0)
    ai_timestamp = Column(DateTime)
    tp_sl_stop_loss_order_id = Column(String(64), nullable=True)
    tp_sl_take_profit_order_id = Column(String(64), nullable=True)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    signal = Column(String(10))
    price = Column(Float)
    amount = Column(Float)
    confidence = Column(String(10))
    reason = Column(Text)
    pnl = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    equity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Engine & Session ────────────────────────────────────────

def _set_wal_mode(dbapi_connection, connection_record):
    """启用 WAL 模式，允许并发读写"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def init_db(db_path: str = None) -> Session:
    """初始化数据库连接并创建所有表"""
    global _engine, _SessionLocal

    path = db_path or DB_PATH
    _engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    event.listen(_engine, "connect", _set_wal_mode)
    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal()


def get_session() -> Session:
    """获取一个新的数据库会话"""
    global _engine, _SessionLocal
    if _engine is None:
        init_db()
    return _SessionLocal()


# ── CRUD Helpers ────────────────────────────────────────────

def upsert_system_status(session: Session, data: dict) -> SystemStatus:
    """写入或更新系统状态（单行 id=1）"""
    row = session.query(SystemStatus).filter_by(id=1).first()
    if row is None:
        row = SystemStatus(id=1)
        session.add(row)
    for key, value in data.items():
        if hasattr(row, key):
            setattr(row, key, value)
    session.commit()
    return row


def insert_trade(session: Session, trade_data: dict) -> Trade:
    """插入一条交易记录"""
    trade = Trade(**trade_data)
    session.add(trade)
    session.commit()

    # 只保留最近 500 条
    count = session.query(Trade).count()
    if count > 500:
        oldest = (
            session.query(Trade)
            .order_by(Trade.id.asc())
            .limit(count - 500)
            .all()
        )
        for t in oldest:
            session.delete(t)
        session.commit()

    return trade


def insert_equity_snapshot(session: Session, equity: float, timestamp: datetime = None) -> EquitySnapshot:
    """插入一条权益快照"""
    snap = EquitySnapshot(
        timestamp=timestamp or datetime.now(),
        equity=equity,
    )
    session.add(snap)
    session.commit()

    # 只保留最近 1000 条
    count = session.query(EquitySnapshot).count()
    if count > 1000:
        oldest = (
            session.query(EquitySnapshot)
            .order_by(EquitySnapshot.id.asc())
            .limit(count - 1000)
            .all()
        )
        for s in oldest:
            session.delete(s)
        session.commit()

    return snap


def get_latest_status(session: Session) -> Optional[SystemStatus]:
    """获取当前系统状态"""
    return session.query(SystemStatus).filter_by(id=1).first()


def get_recent_trades(session: Session, limit: int = 500) -> List[Trade]:
    """获取最近 N 条交易记录"""
    return (
        session.query(Trade)
        .order_by(Trade.id.desc())
        .limit(limit)
        .all()
    )


def get_equity_snapshots(session: Session, limit: int = 1000) -> List[EquitySnapshot]:
    """获取最近 N 条权益快照"""
    return (
        session.query(EquitySnapshot)
        .order_by(EquitySnapshot.id.asc())
        .limit(limit)
        .all()
    )


def calculate_performance_from_db(session: Session) -> dict:
    """从 DB 计算交易绩效"""
    trades = session.query(Trade).all()
    if not trades:
        return {
            "total_pnl": 0,
            "win_rate": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
        }
    total_pnl = sum(t.pnl for t in trades)
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.pnl > 0)
    losing_trades = sum(1 for t in trades if t.pnl < 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades else 0
    return {
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
    }


if __name__ == "__main__":
    session = init_db()
    print("数据库表创建成功")
    print(f"路径: {DB_PATH}")
    print(f"表: {Base.metadata.tables.keys()}")
