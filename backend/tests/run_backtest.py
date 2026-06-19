"""
回测工具 — 用本地 K 线数据跑策略

用法:
  python tests/run_backtest.py                           # 默认 BTC 3m 技术指标
  python tests/run_backtest.py --symbol ETH --tf 1h      # 指定币种周期
  python tests/run_backtest.py --symbol DOGE --tf 3m --mode demo
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from datetime import datetime

from app.services.strategies.strategy_technical import TechnicalStrategy
from app.services.backtest.engine import run_backtest

ROOT = Path(__file__).resolve().parent.parent
KLINE_DIR = ROOT / "data" / "kline"
RESULT_DIR = ROOT / "data" / "backtest"
RESULT_DIR.mkdir(parents=True, exist_ok=True)


def find_kline_file(symbol: str, tf: str, mode: str) -> Path | None:
    """在 data/kline/{mode}/{symbol}/ 下匹配文件。"""
    name = symbol.split("/")[0].lower()
    pattern = f"{name}_{tf}_"
    subdir = KLINE_DIR / mode / name
    if not subdir.exists():
        return None
    files = sorted(subdir.glob(f"{pattern}*.csv"))
    return files[-1] if files else None  # 取最新的一个


def run(symbol: str, tf: str, mode: str, capital: float, pos_ratio: float, fee: float):
    filepath = find_kline_file(symbol, tf, mode)
    if filepath is None:
        print(f"未找到数据: {symbol} {tf} ({mode})")
        return

    print(f"数据: {filepath}")
    df = pd.read_csv(filepath)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"K线: {len(df)} 根  {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")

    strategy = TechnicalStrategy()

    result = run_backtest(
        df, strategy,
        initial_capital=capital,
        position_ratio=pos_ratio,
        fee_rate=fee,
        warmup=50,
        timeframe=tf,
    )

    metrics = result["metrics"]
    trades = result["trades"]
    equity = result["equity_curve"]

    # ── 打印 ──
    print(f"\n{'='*50}")
    print(f"回测结果: {symbol} {tf}")
    print(f"{'='*50}")
    print(f"初始资金: ${capital:.0f}")
    print(f"最终权益: ${metrics['final_equity']:.2f}")
    print(f"总收益率: {metrics['total_return_pct']:.2f}%")
    print(f"胜率:     {metrics['win_rate']:.2f}%")
    print(f"盈亏比:   {metrics['profit_factor']:.2f}")
    print(f"最大回撤: {metrics['max_drawdown_pct']:.2f}%")
    print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"交易次数: {metrics['total_trades']} (盈{metrics['winning_trades']} 亏{metrics['losing_trades']})")
    print(f"平均盈亏: ${metrics['avg_trade_pnl']:.2f}")

    # ── 保存 ──
    name = symbol.split("/")[0].lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RESULT_DIR / f"{name}_{tf}_{mode}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 权益曲线
    pd.DataFrame(equity).to_csv(run_dir / "equity_curve.csv", index=False)
    # 交易记录
    pd.DataFrame(trades).to_csv(run_dir / "trades.csv", index=False)
    # 指标摘要
    summary = pd.DataFrame([metrics])
    summary.to_csv(run_dir / "metrics.csv", index=False)

    # 文本报告
    report = []
    report.append(f"# 回测报告: {symbol} {tf}")
    report.append(f"")
    report.append(f"- 数据文件: {filepath.name}")
    report.append(f"- K线数量: {len(df)}")
    report.append(f"- 数据范围: {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")
    report.append(f"- 初始资金: ${capital:.0f}")
    report.append(f"- 手续费: {fee*100:.2f}%")
    report.append(f"")
    report.append(f"## 核心指标")
    report.append(f"")
    report.append(f"| 指标 | 值 |")
    report.append(f"|------|-----|")
    report.append(f"| 最终权益 | ${metrics['final_equity']:.2f} |")
    report.append(f"| 总收益率 | {metrics['total_return_pct']:.2f}% |")
    report.append(f"| 胜率 | {metrics['win_rate']:.2f}% |")
    report.append(f"| 盈亏比 | {metrics['profit_factor']:.2f} |")
    report.append(f"| 最大回撤 | {metrics['max_drawdown_pct']:.2f}% |")
    report.append(f"| 夏普比率 | {metrics['sharpe_ratio']:.2f} |")
    report.append(f"| 交易次数 | {metrics['total_trades']} |")
    report.append(f"| 盈利次数 | {metrics['winning_trades']} |")
    report.append(f"| 亏损次数 | {metrics['losing_trades']} |")
    report.append(f"| 平均盈亏 | ${metrics['avg_trade_pnl']:.2f} |")

    (run_dir / "report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"\n报告已保存: {run_dir}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="策略回测")
    p.add_argument("--symbol", default="BTC/USDT:USDT")
    p.add_argument("--tf", default="3m")
    p.add_argument("--mode", default="live", choices=["live", "demo"])
    p.add_argument("--capital", type=float, default=1000)
    p.add_argument("--pos-ratio", type=float, default=0.5)
    p.add_argument("--fee", type=float, default=0.001)
    args = p.parse_args()
    run(args.symbol, args.tf, args.mode, args.capital, args.pos_ratio, args.fee)


if __name__ == "__main__":
    main()
