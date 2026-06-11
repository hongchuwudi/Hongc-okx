"""
Created: 2026-06-06
Author: hongchuwudi
Description: 回测引擎 — 逐 K 线重放策略，模拟真实交易

Contains:
- Function: run_backtest_stream — 生成器版，逐 K 线 yield 进度事件，支持 SSE 流式推送
- Function: run_backtest — 批量版，返回完整交易记录、权益曲线和性能指标字典
"""

import pandas as pd
from typing import Optional

from app.strategies.base import BaseStrategy
from app.services.backtest.engine_helpers import _check_stop, _close_position, _to_native, _to_ms
from app.services.backtest.engine_metrics import _compute_metrics


# 逐根 K 线重放策略逻辑（生成器版），每根 K 线 yield 一次进度事件，支持 SSE 流式推送到前端。
# yield 格式: {"type":"progress","bar":1,"total":200,"price":0.1,"equity":205,"signal":"BUY","trade":{...},"position":"long",...}
# 最后 yield: {"type":"done","trades":[...],"equity_curve":[...],"metrics":{...}}
def run_backtest_stream(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    initial_capital: float = 100.0,
    position_ratio: float = 0.5,
    fee_rate: float = 0.001,
    warmup: int = 50,
    timeframe: str = "1h",
):
    if len(df) < warmup + 5:
        yield {"type": "error", "message": f"数据不足，需要至少 {warmup + 5} 条 K 线，实际 {len(df)} 条"}
        return

    df = df.reset_index(drop=True)
    capital = initial_capital
    position: Optional[dict] = None
    trades: list = []
    # 记录初始权益点，确保回撤计算包含完整的资本变化
    first_ts = _to_ms(df.iloc[0]["timestamp"])
    equity_curve: list = [{"bar": 0, "timestamp": first_ts, "equity": initial_capital}]
    total_bars = len(df) - warmup

    for i in range(warmup, len(df)):
        window = df.iloc[: i + 1].copy()
        bar = df.iloc[i]
        price = float(bar["close"])
        high = float(bar.get("high", price))
        low = float(bar.get("low", price))
        ts = _to_ms(bar["timestamp"])

        stopped_out = _check_stop(price, high, low, position)
        trade_event = None

        if stopped_out:
            pnl = _close_position(position, stopped_out, fee_rate) - position.get("entry_fee", 0)
            capital += position["size"] * stopped_out - (position["size"] * stopped_out * fee_rate)
            trade_event = {
                "bar": i, "timestamp": ts, "side": position["side"],
                "entry": position["entry_price"], "exit": stopped_out,
                "size": position["size"], "pnl": round(pnl, 4),
                "bars_held": i - position["entry_bar"],
                "confidence": "TP/SL",
            }
            trades.append(trade_event)
            position = None
        else:
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
                if sig in ("BUY", "SELL"):
                    trade_capital = capital * position_ratio
                    size = trade_capital / price
                    fee = trade_capital * fee_rate
                    capital -= trade_capital
                    capital -= fee
                    side = "long" if sig == "BUY" else "short"
                    position = {
                        "side": side, "size": size, "entry_price": price,
                        "entry_bar": i, "stop_loss": sl, "take_profit": tp,
                        "entry_fee": fee,
                    }
                    trade_event = {
                        "bar": i, "timestamp": ts, "side": side,
                        "entry": price, "size": size, "pnl": 0,
                        "bars_held": 0, "confidence": confidence, "action": "open",
                    }
            else:
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
                    pnl -= fee + position.get("entry_fee", 0)
                    capital += gross - fee
                    trade_event = {
                        "bar": i, "timestamp": ts, "side": position["side"],
                        "entry": position["entry_price"], "exit": price,
                        "size": position["size"], "pnl": round(pnl, 4),
                        "bars_held": i - position["entry_bar"],
                        "confidence": confidence, "action": "close",
                    }
                    trades.append(trade_event)
                    position = None

        # 权益 = 现金 + 持仓市值（当前价格），不含未实现盈亏的重复计算
        if position:
            equity = round(capital + position["size"] * price, 2)
        else:
            equity = round(capital, 2)
        equity_curve.append({"bar": i, "timestamp": ts, "equity": equity})

        yield {
            "type": "progress",
            "bar": i - warmup + 1,
            "total": total_bars,
            "price": round(price, 8),
            "equity": equity,
            "signal": sig,
            "confidence": confidence,
            "position_side": position["side"] if position else None,
            "trades_count": len(trades),
            "timestamp": ts,
            "trade": trade_event,
        }

    if position and len(df) > 0:
        last_bar = df.iloc[-1]
        last_price = float(last_bar["close"])
        last_ts = _to_ms(last_bar["timestamp"])
        gross = position["size"] * last_price
        fee = gross * fee_rate
        if position["side"] == "long":
            pnl = (last_price - position["entry_price"]) * position["size"] - fee - position.get("entry_fee", 0)
        else:
            pnl = (position["entry_price"] - last_price) * position["size"] - fee - position.get("entry_fee", 0)
        capital += gross - fee
        trades.append({
            "bar": len(df) - 1, "timestamp": last_ts, "side": position["side"],
            "entry": position["entry_price"], "exit": last_price,
            "size": position["size"], "pnl": round(pnl, 4),
            "bars_held": len(df) - 1 - position["entry_bar"],
            "confidence": "FORCED_CLOSE", "action": "close",
        })
        equity_curve.append({"bar": len(df) - 1, "timestamp": last_ts, "equity": round(capital, 2)})

    metrics = _compute_metrics(trades, equity_curve, initial_capital, timeframe)
    native = _to_native({"trades": trades, "equity_curve": equity_curve, "metrics": metrics})
    yield {"type": "done", **native}


# 逐根 K 线重放策略逻辑，模拟真实交易。 每根 K 线先检测止盈止损是否触发，再生成交易信号。 支持 TechnicalStrategy 和 DeepSeekStrategy。 返回包含交易记录、权益曲线和性能指标的字典。
def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    initial_capital: float = 100.0,
    position_ratio: float = 0.5,
    fee_rate: float = 0.001,
    warmup: int = 50,
    timeframe: str = "1h",
) -> dict:
    if len(df) < warmup + 5:
        raise ValueError(f"数据不足，需要至少 {warmup + 5} 条 K 线，实际 {len(df)} 条")

    df = df.reset_index(drop=True)
    capital = initial_capital
    position: Optional[dict] = None
    trades: list = []
    first_ts = _to_ms(df.iloc[0]["timestamp"])
    equity_curve: list = [{"bar": 0, "timestamp": first_ts, "equity": initial_capital}]

    for i in range(warmup, len(df)):
        window = df.iloc[: i + 1].copy()
        bar = df.iloc[i]
        price = float(bar["close"])
        high = float(bar.get("high", price))
        low = float(bar.get("low", price))
        ts = _to_ms(bar["timestamp"])

        stopped_out = _check_stop(price, high, low, position)

        if stopped_out:
            pnl = _close_position(position, stopped_out, fee_rate) - position.get("entry_fee", 0)
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
                if sig in ("BUY", "SELL"):
                    trade_capital = capital * position_ratio
                    size = trade_capital / price
                    fee = trade_capital * fee_rate
                    capital -= trade_capital
                    capital -= fee
                    side = "long" if sig == "BUY" else "short"
                    position = {
                        "side": side, "size": size, "entry_price": price,
                        "entry_bar": i, "stop_loss": sl, "take_profit": tp,
                        "entry_fee": fee,
                    }

            else:
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
                    pnl -= fee + position.get("entry_fee", 0)
                    capital += gross - fee
                    trades.append({
                        "bar": i, "timestamp": ts, "side": position["side"],
                        "entry": position["entry_price"], "exit": price,
                        "size": position["size"], "pnl": round(pnl, 4),
                        "bars_held": i - position["entry_bar"],
                        "confidence": confidence,
                    })
                    position = None

        if position:
            equity = round(capital + position["size"] * price, 2)
        else:
            equity = round(capital, 2)
        equity_curve.append({
            "bar": i, "timestamp": ts, "equity": equity,
        })

    if position and len(df) > 0:
        last_bar = df.iloc[-1]
        last_price = float(last_bar["close"])
        last_ts = _to_ms(last_bar["timestamp"])
        gross = position["size"] * last_price
        fee = gross * fee_rate
        if position["side"] == "long":
            pnl = (last_price - position["entry_price"]) * position["size"] - fee - position.get("entry_fee", 0)
        else:
            pnl = (position["entry_price"] - last_price) * position["size"] - fee - position.get("entry_fee", 0)
        capital += gross - fee
        trades.append({
            "bar": len(df) - 1, "timestamp": last_ts, "side": position["side"],
            "entry": position["entry_price"], "exit": last_price,
            "size": position["size"], "pnl": round(pnl, 4),
            "bars_held": len(df) - 1 - position["entry_bar"],
            "confidence": "FORCED_CLOSE",
        })
        equity_curve.append({"bar": len(df) - 1, "timestamp": last_ts, "equity": round(capital, 2)})

    metrics = _compute_metrics(trades, equity_curve, initial_capital, timeframe)
    return _to_native({"trades": trades, "equity_curve": equity_curve, "metrics": metrics})
