"""
Created: 2026-06-14
Author: hongchuwudi
Description: 回测性能指标计算 — 收益率、胜率、盈亏比、最大回撤、夏普比率等

Contains:
- Function: _bars_per_year — 根据 K 线周期计算每年 K 线数
- Function: _compute_metrics — 根据交易记录和权益曲线计算全部性能指标
"""

import numpy as np
import pandas as pd

from app.services.backtest.engine_helpers import _to_native


def _bars_per_year(timeframe: str) -> int:
    """根据 K 线周期返回每年 K 线数，用于夏普比率年化"""
    t = timeframe.lower()
    if t.endswith("m"):
        minutes = int(t[:-1])
        return 365 * 24 * 60 // minutes
    if t.endswith("h"):
        hours = int(t[:-1])
        return 365 * 24 // hours
    if t.endswith("d"):
        days = int(t[:-1])
        return 365 // days
    return 8760  # fallback: 小时


def _compute_metrics(trades: list, equity_curve: list, initial_capital: float, timeframe: str = "1h") -> dict:
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

    if len(equity_curve) > 1:
        eqs = pd.Series([e["equity"] for e in equity_curve])
        returns = eqs.pct_change().dropna()
        # 根据 K 线周期计算年化系数
        bars_per_year = _bars_per_year(timeframe)
        sharpe = (returns.mean() / returns.std()) * np.sqrt(bars_per_year) if returns.std() > 0 else 0.0
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
