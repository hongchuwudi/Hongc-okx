"""
数据管理模块 - 用于在交易程序和Web界面之间共享数据

DB 主存储 + JSON fallback
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from database import (
    get_session,
    upsert_system_status,
    insert_trade,
    insert_equity_snapshot,
    get_latest_status,
    get_recent_trades,
    get_equity_snapshots,
    calculate_performance_from_db,
)
from logger import get_logger

logger = get_logger()

DATA_FILE = "trading_data.json"
TRADES_FILE = "trades_history.json"
EQUITY_HISTORY_FILE = "equity_history.json"

def save_trading_data(data: Dict):
    """保存交易数据 (JSON, 保留兼容)"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存交易数据失败: {e}")

def load_trading_data() -> Optional[Dict]:
    """加载交易数据 (JSON fallback)"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"加载交易数据失败: {e}")
        return None

def save_trade_record(trade: Dict):
    """保存交易记录 (JSON, 保留兼容)"""
    try:
        trades = []
        if os.path.exists(TRADES_FILE):
            with open(TRADES_FILE, 'r', encoding='utf-8') as f:
                trades = json.load(f)
        trades.append(trade)
        if len(trades) > 500:
            trades = trades[-500:]
        with open(TRADES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存交易记录失败: {e}")

def load_trades_history() -> List[Dict]:
    """加载交易历史 (JSON fallback)"""
    try:
        if os.path.exists(TRADES_FILE):
            with open(TRADES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"加载交易历史失败: {e}")
        return []

def calculate_performance(trades: List[Dict]) -> Dict:
    """计算交易绩效"""
    if not trades:
        return {
            'total_pnl': 0,
            'win_rate': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
    total_pnl = sum(t.get('pnl', 0) for t in trades)
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
    losing_trades = sum(1 for t in trades if t.get('pnl', 0) < 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades
    }

def save_equity_snapshot(equity: float, timestamp: str = None):
    """保存账户权益快照 (JSON, 保留兼容)"""
    try:
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        equity_history = []
        if os.path.exists(EQUITY_HISTORY_FILE):
            with open(EQUITY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                equity_history = json.load(f)
        equity_history.append({
            'timestamp': timestamp,
            'equity': equity
        })
        if len(equity_history) > 1000:
            equity_history = equity_history[-1000:]
        with open(EQUITY_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(equity_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存权益快照失败: {e}")

def load_equity_history() -> List[Dict]:
    """加载账户权益历史 (JSON fallback)"""
    try:
        if os.path.exists(EQUITY_HISTORY_FILE):
            with open(EQUITY_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"加载权益历史失败: {e}")
        return []


# ── DB 写入函数 ──────────────────────────────────────────────

def save_system_status_to_db(
    status: str,
    account_info: Optional[Dict] = None,
    btc_info: Optional[Dict] = None,
    position: Optional[Dict] = None,
    ai_signal: Optional[Dict] = None,
    tp_sl_orders: Optional[Dict] = None,
):
    """将系统状态写入 SQLite (代替原来的 update_system_status)"""
    try:
        session = get_session()
        data = {
            "status": status,
            "last_update": datetime.now(),
        }
        if account_info:
            data["balance"] = account_info.get("balance", 0)
            data["equity"] = account_info.get("equity", 0)
            data["leverage"] = account_info.get("leverage", 1)
        if btc_info:
            data["btc_price"] = btc_info.get("price", 0)
            data["btc_change"] = btc_info.get("change", 0)
            data["timeframe"] = btc_info.get("timeframe", "1h")
            data["mode"] = btc_info.get("mode", "cross-oneway")
        if position is not None:
            if position:
                data["position_side"] = position.get("side")
                data["position_size"] = position.get("size", 0)
                data["position_entry_price"] = position.get("entry_price", 0)
                data["position_unrealized_pnl"] = position.get("unrealized_pnl", 0)
            else:
                data["position_side"] = None
                data["position_size"] = 0
                data["position_entry_price"] = 0
                data["position_unrealized_pnl"] = 0
        if ai_signal:
            data["ai_signal"] = ai_signal.get("signal", "HOLD")
            data["ai_confidence"] = ai_signal.get("confidence", "N/A")
            data["ai_reason"] = ai_signal.get("reason", "")
            data["ai_stop_loss"] = ai_signal.get("stop_loss", 0)
            data["ai_take_profit"] = ai_signal.get("take_profit", 0)
            data["ai_timestamp"] = datetime.now()
        if tp_sl_orders is not None:
            data["tp_sl_stop_loss_order_id"] = tp_sl_orders.get("stop_loss_order_id")
            data["tp_sl_take_profit_order_id"] = tp_sl_orders.get("take_profit_order_id")

        upsert_system_status(session, data)
        session.close()

        if account_info and "equity" in account_info:
            save_equity_snapshot_to_db(account_info["equity"])

    except Exception as e:
        logger.error(f"保存系统状态到DB失败: {e}")


def save_trade_record_to_db(trade: Dict):
    """将交易记录写入 SQLite"""
    try:
        session = get_session()
        ts = trade.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                ts = datetime.now()
        elif ts is None:
            ts = datetime.now()

        insert_trade(session, {
            "timestamp": ts,
            "signal": trade.get("signal", "HOLD"),
            "price": trade.get("price", 0),
            "amount": trade.get("amount", 0),
            "confidence": trade.get("confidence", "N/A"),
            "reason": trade.get("reason", ""),
            "pnl": trade.get("pnl", 0),
        })
        session.close()
    except Exception as e:
        logger.error(f"保存交易记录到DB失败: {e}")


def save_equity_snapshot_to_db(equity: float, timestamp: str = None):
    """将权益快照写入 SQLite"""
    try:
        session = get_session()
        ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") if timestamp else datetime.now()
        insert_equity_snapshot(session, equity, ts)
        session.close()
    except Exception as e:
        logger.error(f"保存权益快照到DB失败: {e}")


# ── DB 读取函数 (供 Streamlit 使用) ─────────────────────────

def load_trading_data_from_db() -> Optional[Dict]:
    """从 SQLite 加载当前状态，返回兼容旧 dict 格式"""
    try:
        session = get_session()
        row = get_latest_status(session)
        if row is None:
            session.close()
            return None

        data = {
            "status": row.status,
            "last_update": row.last_update.strftime("%Y-%m-%d %H:%M:%S") if row.last_update else "",
            "account": {
                "balance": row.balance,
                "equity": row.equity,
                "leverage": row.leverage,
            },
            "btc": {
                "price": row.btc_price,
                "change": row.btc_change,
                "timeframe": row.timeframe,
                "mode": row.mode,
            },
            "position": None,
            "performance": calculate_performance_from_db(session),
            "ai_signal": {
                "signal": row.ai_signal,
                "confidence": row.ai_confidence,
                "reason": row.ai_reason,
                "stop_loss": row.ai_stop_loss,
                "take_profit": row.ai_take_profit,
                "timestamp": row.ai_timestamp.strftime("%Y-%m-%d %H:%M:%S") if row.ai_timestamp else "N/A",
            },
            "tp_sl_orders": {
                "stop_loss_order_id": row.tp_sl_stop_loss_order_id,
                "take_profit_order_id": row.tp_sl_take_profit_order_id,
            },
        }
        if row.position_side:
            data["position"] = {
                "side": row.position_side,
                "size": row.position_size,
                "entry_price": row.position_entry_price,
                "unrealized_pnl": row.position_unrealized_pnl,
            }
        session.close()
        return data
    except Exception as e:
        logger.error(f"从DB加载数据失败: {e}")
        return None


def load_trades_history_from_db() -> List[Dict]:
    """从 SQLite 加载交易历史"""
    try:
        session = get_session()
        trades = get_recent_trades(session, 500)
        result = [
            {
                "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S") if t.timestamp else "",
                "signal": t.signal,
                "price": t.price,
                "amount": t.amount,
                "confidence": t.confidence,
                "reason": t.reason,
                "pnl": t.pnl,
            }
            for t in trades
        ]
        session.close()
        return result
    except Exception as e:
        logger.error(f"从DB加载交易历史失败: {e}")
        return []


def load_equity_history_from_db() -> List[Dict]:
    """从 SQLite 加载权益历史"""
    try:
        session = get_session()
        snaps = get_equity_snapshots(session, 1000)
        result = [
            {
                "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S") if s.timestamp else "",
                "equity": s.equity,
            }
            for s in snaps
        ]
        session.close()
        return result
    except Exception as e:
        logger.error(f"从DB加载权益历史失败: {e}")
        return []


def update_system_status(
    status: str,
    account_info: Optional[Dict] = None,
    btc_info: Optional[Dict] = None,
    position: Optional[Dict] = None,
    ai_signal: Optional[Dict] = None,
    tp_sl_orders: Optional[Dict] = None
):
    """更新系统状态 — 优先写 DB，fallback 写 JSON"""
    save_system_status_to_db(status, account_info, btc_info, position, ai_signal, tp_sl_orders)

