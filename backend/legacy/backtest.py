#!/usr/bin/env python
"""
简易回测引擎 — 用历史 K 线数据重放策略，模拟交易并计算绩效指标

用法:
    python backtest.py --strategy technical --download --limit 2000
    python backtest.py --strategy technical --data btc_1h.csv --capital 100
    python backtest.py --strategy deepseek --data btc_1h.csv   (需要 DEEPSEEK_API_KEY)
"""
import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_strategy import BaseStrategy
from technical_strategy import TechnicalStrategy
from logger import get_logger

logger = get_logger()


# ── 回测引擎 ────────────────────────────────────────────────

def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    initial_capital: float = 100.0,
    position_ratio: float = 0.5,
    fee_rate: float = 0.001,
    warmup: int = 200,
) -> dict:
    """
    逐根 K 线重放回测。

    Args:
        df: OHLCV DataFrame, columns: [timestamp, open, high, low, close, volume]
        strategy: 实现了 generate_signal() 的策略实例
        initial_capital: 初始资金 (USDT)
        position_ratio: 每次开仓占资金的比例
        fee_rate: 手续费率 (默认 0.1%)
        warmup: 预热期 bar 数

    Returns:
        dict with keys: trades, equity_curve, metrics
    """
    if len(df) < warmup + 10:
        raise ValueError(f"数据不足，需要至少 {warmup + 10} 条 K 线，实际 {len(df)} 条")

    df = df.reset_index(drop=True)
    capital = initial_capital
    position: Optional[dict] = None  # {side, size, entry_price, entry_bar}
    trades: List[dict] = []
    equity_curve: List[dict] = []

    for i in range(warmup, len(df)):
        window = df.iloc[: i + 1].copy()
        bar = df.iloc[i]
        price = float(bar["close"])
        ts = bar.get("timestamp", i)

        # 生成信号
        try:
            signal = strategy.generate_signal(window, position)
        except Exception:
            signal = {"signal": "HOLD", "confidence": "LOW", "reason": "error",
                      "stop_loss": price * 0.98, "take_profit": price * 1.02}

        sig = signal.get("signal", "HOLD")
        confidence = signal.get("confidence", "MEDIUM")

        # ── 执行交易逻辑 ──
        pnl = 0.0

        if position is None:
            # 无持仓 → 开仓
            if sig == "BUY":
                trade_capital = capital * position_ratio
                size = trade_capital / price
                cost = size * price * fee_rate
                capital -= cost
                position = {"side": "long", "size": size, "entry_price": price, "entry_bar": i}
            elif sig == "SELL":
                trade_capital = capital * position_ratio
                size = trade_capital / price
                cost = size * price * fee_rate
                capital -= cost
                position = {"side": "short", "size": size, "entry_price": price, "entry_bar": i}

        elif position["side"] == "long":
            # 持有多仓
            if sig == "SELL":
                # 平仓
                gross = position["size"] * price
                fee = gross * fee_rate
                pnl = (price - position["entry_price"]) * position["size"] - fee - (
                    position["size"] * position["entry_price"] * fee_rate
                )
                capital += gross - fee
                trades.append({
                    "timestamp": ts, "side": "long", "entry": position["entry_price"],
                    "exit": price, "size": position["size"], "pnl": pnl,
                    "bars": i - position["entry_bar"], "confidence": confidence,
                })
                position = None
            elif sig == "BUY" and confidence == "LOW":
                pass  # 同方向低信心不加仓

        elif position["side"] == "short":
            # 持有空仓
            if sig == "BUY":
                # 平仓
                buyback = position["size"] * price
                fee = buyback * fee_rate
                pnl = (position["entry_price"] - price) * position["size"] - fee - (
                    position["size"] * position["entry_price"] * fee_rate
                )
                capital += buyback - fee
                trades.append({
                    "timestamp": ts, "side": "short", "entry": position["entry_price"],
                    "exit": price, "size": position["size"], "pnl": pnl,
                    "bars": i - position["entry_bar"], "confidence": confidence,
                })
                position = None

        # ── 记录权益曲线 ──
        unrealized = 0.0
        if position:
            if position["side"] == "long":
                unrealized = (price - position["entry_price"]) * position["size"]
            else:
                unrealized = (position["entry_price"] - price) * position["size"]
        equity_curve.append({"timestamp": ts, "equity": capital + unrealized})

    # 强制平仓（如果有未平仓位）
    if position and len(df) > 0:
        last_price = float(df["close"].iloc[-1])
        if position["side"] == "long":
            pnl = (last_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - last_price) * position["size"]
        capital += pnl
        trades.append({
            "timestamp": df.iloc[-1].get("timestamp", len(df)),
            "side": position["side"], "entry": position["entry_price"],
            "exit": last_price, "size": position["size"], "pnl": pnl,
            "bars": len(df) - position["entry_bar"],
            "confidence": "FORCED_CLOSE",
        })
        position = None

    # ── 计算指标 ──
    metrics = _compute_metrics(trades, equity_curve, initial_capital)

    return {"trades": trades, "equity_curve": equity_curve, "metrics": metrics}


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

    # 夏普比率（年化）
    if len(equity_curve) > 1:
        eqs = pd.Series([e["equity"] for e in equity_curve])
        returns = eqs.pct_change().dropna()
        if returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(8760)  # 年化（小时）
        else:
            sharpe = 0.0
    else:
        sharpe = 0.0

    # 平均持仓时间
    avg_bars = sum(t.get("bars", 1) for t in trades) / total_trades if total_trades else 0

    return {
        "initial_capital": initial_capital,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return, 2),
        "total_trades": total_trades,
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "avg_trade_pnl": round(avg_trade, 4),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "avg_bars_held": round(avg_bars, 1),
    }


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="量化策略回测引擎")
    parser.add_argument("--strategy", default="technical", choices=["technical", "deepseek"],
                        help="策略 (默认: technical)")
    parser.add_argument("--data", help="OHLCV CSV 文件路径")
    parser.add_argument("--download", action="store_true", help="从 OKX 下载历史数据")
    parser.add_argument("--symbol", default="BTC/USDT:USDT", help="交易对")
    parser.add_argument("--timeframe", default="1h", help="K 线周期")
    parser.add_argument("--limit", type=int, default=2000, help="下载 K 线数量")
    parser.add_argument("--capital", type=float, default=100.0, help="初始资金 USDT")
    parser.add_argument("--position-ratio", type=float, default=0.5, help="仓位比例")
    parser.add_argument("--fee", type=float, default=0.001, help="手续费率")
    parser.add_argument("--warmup", type=int, default=200, help="预热 K 线条数")
    parser.add_argument("--output", help="导出权益曲线到 CSV")
    args = parser.parse_args()

    # 加载数据
    if args.download:
        logger.info(f"从 OKX 下载 {args.symbol} {args.timeframe} K 线 × {args.limit} ...")
        try:
            import ccxt
            exchange = ccxt.okx()
            ohlcv = exchange.fetch_ohlcv(args.symbol, args.timeframe, limit=args.limit)
            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        except Exception as e:
            logger.error(f"下载失败: {e}")
            sys.exit(1)
    elif args.data:
        logger.info(f"从文件加载: {args.data}")
        df = pd.read_csv(args.data)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
    else:
        parser.error("请指定 --data 或 --download")

    # 初始化策略
    if args.strategy == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logger.error("DeepSeek 策略需要设置 DEEPSEEK_API_KEY 环境变量")
            sys.exit(1)
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        from deepseek_strategy import DeepSeekStrategy
        strategy = DeepSeekStrategy(
            {"symbol": args.symbol, "timeframe": args.timeframe, "leverage": 1},
            client,
        )
    else:
        strategy = TechnicalStrategy()

    logger.info(f"策略: {strategy.name}")
    logger.info(f"数据: {len(df)} 条 K 线, {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")

    # 运行回测
    result = run_backtest(
        df, strategy,
        initial_capital=args.capital,
        position_ratio=args.position_ratio,
        fee_rate=args.fee,
        warmup=args.warmup,
    )

    # 输出结果
    m = result["metrics"]
    print("\n" + "=" * 50)
    print("  回测结果")
    print("=" * 50)
    print(f"  策略:        {strategy.name}")
    print(f"  K线范围:     {df['timestamp'].iloc[args.warmup]} ~ {df['timestamp'].iloc[-1]}")
    print(f"  数据量:      {len(df)} 条 ({len(df) - args.warmup} 条有效)")
    print(f"  初始资金:    {m['initial_capital']:.2f} USDT")
    print(f"  最终权益:    {m['final_equity']:.2f} USDT")
    print(f"  总收益率:    {m['total_return_pct']:+.2f}%")
    print(f"  总交易次数:  {m['total_trades']}")
    print(f"  胜率:        {m['win_rate']:.1f}%")
    print(f"  盈亏比:      {m['profit_factor']:.2f}")
    print(f"  最大回撤:    {m['max_drawdown_pct']:.2f}%")
    print(f"  夏普比率:    {m['sharpe_ratio']:.2f}")
    print(f"  平均盈亏:    {m['avg_trade_pnl']:.4f} USDT")
    print(f"  平均盈利:    {m['avg_win']:.4f} USDT")
    print(f"  平均亏损:    {m['avg_loss']:.4f} USDT")
    print(f"  平均持仓:    {m['avg_bars_held']:.1f} 根K线")
    print("=" * 50)

    if args.output:
        pd.DataFrame(result["equity_curve"]).to_csv(args.output, index=False)
        logger.info(f"权益曲线已导出: {args.output}")

    if args.download and not args.output:
        # 自动保存一份下载的数据
        csv_path = f"ohlcv_{args.symbol.replace('/', '_')}_{args.timeframe}.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"K线数据已保存: {csv_path}")


if __name__ == "__main__":
    main()
