"""回测引擎 — 逐 K 线重放策略，模拟交易"""

import numpy as np
import pandas as pd
from typing import Any, Dict, Optional

from app.strategies.base import BaseStrategy


def _to_native(v: Any) -> Any:
    """递归转换 numpy 类型为 Python 原生类型，防止 PostgreSQL 写入报错"""
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, dict):
        return {k: _to_native(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_to_native(x) for x in v]
    return v


def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    initial_capital: float = 100.0,
    position_ratio: float = 0.5,
    fee_rate: float = 0.001,
    warmup: int = 50,
) -> dict:
    """
    逐根 K 线重放。

    每根 K 线先检测止盈止损，再生成信号。支持 TechnicalStrategy 和 DeepSeekStrategy。
    """
    if len(df) < warmup + 5:
        raise ValueError(f"数据不足，需要至少 {warmup + 5} 条 K 线，实际 {len(df)} 条")

    df = df.reset_index(drop=True)
    capital = initial_capital
    position: Optional[dict] = None
    trades: list = []
    equity_curve: list = []

    for i in range(warmup, len(df)):
        window = df.iloc[: i + 1].copy()
        bar = df.iloc[i]
        price = float(bar["close"])
        high = float(bar.get("high", price))
        low = float(bar.get("low", price))
        ts = str(bar.get("timestamp", i))

        # ── 止盈止损检测 ──
        stopped_out = _check_stop(price, high, low, position)

        if stopped_out:
            pnl = _close_position(position, stopped_out, fee_rate)
            capital += position["size"] * stopped_out - (position["size"] * stopped_out * fee_rate)
            trades.append({
                "bar": i, "timestamp": ts, "side": position["side"],
                "entry": position["entry_price"], "exit": stopped_out,
                "size": position["size"], "pnl": round(pnl, 4),
                "bars_held": i - position["entry_bar"],
                "confidence": "TP/SL",
            })
            position = None

        else:
            # 生成信号
            try:
                signal = strategy.generate_signal(window, position)
            except Exception:
                signal = {
                    "signal": "HOLD", "confidence": "LOW", "reason": "error",
                    "stop_loss": price * 0.98, "take_profit": price * 1.02,
                }

            sig = signal.get("signal", "HOLD")
            confidence = signal.get("confidence", "MEDIUM")
            sl = signal.get("stop_loss", price * 0.98)
            tp = signal.get("take_profit", price * 1.02)

            if position is None:
                # 无持仓 → 开仓（扣除本金 + 手续费）
                if sig in ("BUY", "SELL"):
                    trade_capital = capital * position_ratio
                    size = trade_capital / price
                    fee = trade_capital * fee_rate
                    capital -= trade_capital  # 扣除买入本金
                    capital -= fee             # 扣除手续费
                    side = "long" if sig == "BUY" else "short"
                    position = {
                        "side": side, "size": size, "entry_price": price,
                        "entry_bar": i, "stop_loss": sl, "take_profit": tp,
                    }

            else:
                # 有持仓 → 检查是否平仓
                should_close = (
                    (position["side"] == "long" and sig == "SELL") or
                    (position["side"] == "short" and sig == "BUY")
                )
                if should_close:
                    gross = position["size"] * price
                    fee = gross * fee_rate
                    if position["side"] == "long":
                        pnl = (price - position["entry_price"]) * position["size"]
                    else:
                        pnl = (position["entry_price"] - price) * position["size"]
                    pnl -= fee
                    capital += gross - fee
                    trades.append({
                        "bar": i, "timestamp": ts, "side": position["side"],
                        "entry": position["entry_price"], "exit": price,
                        "size": position["size"], "pnl": round(pnl, 4),
                        "bars_held": i - position["entry_bar"],
                        "confidence": confidence,
                    })
                    position = None

        # ── 权益曲线 ──
        unrealized = 0.0
        if position:
            if position["side"] == "long":
                unrealized = (price - position["entry_price"]) * position["size"]
            else:
                unrealized = (position["entry_price"] - price) * position["size"]
        equity_curve.append({
            "bar": i, "timestamp": ts, "equity": round(capital + unrealized, 2),
        })

    # 强制平仓
    if position and len(df) > 0:
        last_bar = df.iloc[-1]
        last_price = float(last_bar["close"])
        last_ts = str(last_bar.get("timestamp", len(df) - 1))
        if position["side"] == "long":
            pnl = (last_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - last_price) * position["size"]
        capital += pnl
        trades.append({
            "bar": len(df) - 1, "timestamp": last_ts, "side": position["side"],
            "entry": position["entry_price"], "exit": last_price,
            "size": position["size"], "pnl": round(pnl, 4),
            "bars_held": len(df) - 1 - position["entry_bar"],
            "confidence": "FORCED_CLOSE",
        })

    metrics = _compute_metrics(trades, equity_curve, initial_capital)
    return _to_native({"trades": trades, "equity_curve": equity_curve, "metrics": metrics})


def _check_stop(price: float, high: float, low: float, position: Optional[dict]) -> Optional[float]:
    """检测止盈止损是否触发，返回触发价格，否则 None"""
    if not position:
        return None
    if position["side"] == "long":
        if low <= position["stop_loss"]:
            return position["stop_loss"]
        if high >= position["take_profit"]:
            return position["take_profit"]
    else:
        if high >= position["stop_loss"]:
            return position["stop_loss"]
        if low <= position["take_profit"]:
            return position["take_profit"]
    return None


def _close_position(position: dict, exit_price: float, fee_rate: float) -> float:
    """计算平仓盈亏"""
    if position["side"] == "long":
        pnl = (exit_price - position["entry_price"]) * position["size"]
    else:
        pnl = (position["entry_price"] - exit_price) * position["size"]
    fee = position["size"] * exit_price * fee_rate
    return pnl - fee


def _compute_metrics(trades: list, equity_curve: list, initial_capital: float) -> dict:
    final_equity = equity_curve[-1]["equity"] if equity_curve else initial_capital
    total_return = (final_equity - initial_capital) / initial_capital * 100

    winning = [t for t in trades if t["pnl"] > 0]
    losing = [t for t in trades if t["pnl"] < 0]
    total_trades = len(trades)
    win_rate = len(winning) / total_trades * 100 if total_trades else 0

    gross_profit = sum(t["pnl"] for t in winning) if winning else 0
    gross_loss = abs(sum(t["pnl"] for t in losing)) if losing else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    avg_win = gross_profit / len(winning) if winning else 0
    avg_loss = gross_loss / len(losing) if losing else 0
    avg_trade = sum(t["pnl"] for t in trades) / total_trades if total_trades else 0

    # 最大回撤
    if equity_curve:
        equities = [e["equity"] for e in equity_curve]
        peak = equities[0]
        max_dd = 0.0
        for eq in equities:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_dd:
                max_dd = dd
    else:
        max_dd = 0.0

    # 夏普比率
    if len(equity_curve) > 1:
        eqs = pd.Series([e["equity"] for e in equity_curve])
        returns = eqs.pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(8760) if returns.std() > 0 else 0.0
    else:
        sharpe = 0.0

    avg_bars = sum(t.get("bars_held", 1) for t in trades) / total_trades if total_trades else 0

    return _to_native({
        "initial_capital": float(initial_capital),
        "final_equity": float(round(final_equity, 2)),
        "total_return_pct": float(round(total_return, 2)),
        "total_trades": int(total_trades),
        "winning_trades": int(len(winning)),
        "losing_trades": int(len(losing)),
        "win_rate": float(round(win_rate, 2)),
        "profit_factor": float(round(profit_factor, 2)) if profit_factor != float("inf") else 999.99,
        "max_drawdown_pct": float(round(max_dd, 2)),
        "sharpe_ratio": float(round(sharpe, 2)),
        "avg_trade_pnl": float(round(avg_trade, 4)),
        "avg_win": float(round(avg_win, 4)),
        "avg_loss": float(round(avg_loss, 4)),
        "avg_bars_held": float(round(avg_bars, 1)),
    })
