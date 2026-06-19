"""
Agent 策略回测 — 逐 K 线重放，走完整 engine 流水线

用法:
  python tests/agent_backtest.py
  python tests/agent_backtest.py --symbol DOGE/USDT:USDT --bars 50 --capital 10
"""

import sys, asyncio, json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
KLINE_DIR = ROOT / "data" / "kline"
RESULT_DIR = ROOT / "data" / "backtest"
RESULT_DIR.mkdir(parents=True, exist_ok=True)


def load_data(symbol: str, tf: str, mode: str, bars: int):
    name = symbol.split("/")[0].lower()
    files = sorted((KLINE_DIR / mode / name).glob(f"{name}_{tf}_*.csv"))
    if not files:
        raise FileNotFoundError(f"未找到 {symbol} {tf} ({mode}) 数据")
    df = pd.read_csv(files[-1])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.tail(bars).reset_index(drop=True)


class AgentBacktest:
    """逐 K 线回放，模拟完整 tick 流程。"""

    def __init__(self, df, capital=10, leverage=10, position_ratio=0.8, fee=0.001, warmup=50):
        self.df = df
        self.initial_capital = capital
        self.leverage = leverage
        self.position_ratio = position_ratio
        self.fee = fee
        self.warmup = warmup

        self.capital = capital
        self.position = None  # {"side", "size", "entry_price", "stop_loss", "take_profit"}
        self.trades = []
        self.equity_curve = []

    def _calc_size(self, price):
        """计算仓位大小（考虑杠杆）。"""
        trade_value = self.capital * self.leverage * self.position_ratio
        return trade_value / price

    def _check_stop(self, price, high, low):
        """检查止盈止损是否触发。"""
        if not self.position:
            return None
        sl = self.position["stop_loss"]
        tp = self.position["take_profit"]
        side = self.position["side"]
        if side == "long":
            if low <= sl:
                return sl  # 止损
            if high >= tp:
                return tp  # 止盈
        else:
            if high >= sl:
                return sl
            if low <= tp:
                return tp
        return None

    def _close(self, price, stopped_price, bar_idx, reason):
        """平仓。"""
        pos = self.position
        size = pos["size"]
        if pos["side"] == "long":
            pnl = (price - pos["entry_price"]) * size
        else:
            pnl = (pos["entry_price"] - price) * size
        pnl -= self.fee * size * price * 2  # 开平手续费
        self.capital += pnl
        self.trades.append({
            "bar": bar_idx, "entry": pos["entry_price"], "exit": price,
            "side": pos["side"], "size": size, "pnl": round(pnl, 4),
            "reason": reason,
        })
        self.position = None

    def _open(self, signal, price, bar_idx):
        """开仓。"""
        size = self._calc_size(price)
        fee_cost = self.fee * size * price
        self.capital -= fee_cost  # 开仓手续费
        self.position = {
            "side": "long" if signal == "BUY" else "short",
            "size": size,
            "entry_price": price,
            "stop_loss": price * 0.98,
            "take_profit": price * 1.05,
        }

    async def run(self, coordinator):
        """逐 K 线回放。"""
        total = len(self.df)
        agent_calls = 0
        tech_calls = 0

        for i in range(self.warmup, total):
            window = self.df.iloc[:i + 1]
            bar = self.df.iloc[i]
            price = float(bar["close"])
            high = float(bar.get("high", price))
            low = float(bar.get("low", price))

            # Step 0: 检查止盈止损
            stopped = self._check_stop(price, high, low)
            if stopped:
                self._close(stopped, stopped, i, "TP/SL")
                self.equity_curve.append({"bar": i, "equity": self.capital})
                continue

            # Step 3: 策略分析 — AI 或 技术指标
            try:
                equity = self.capital * self.leverage
                decision = await coordinator.analyze(window, price, equity, self.position)
                agent_calls += 1
            except Exception:
                from app.services.strategies.strategy_technical import TechnicalStrategy
                s = TechnicalStrategy()
                decision = s.generate_signal(window, self.position)
                tech_calls += 1

            sig = decision.get("signal", "HOLD")

            if self.position is None:
                if sig in ("BUY", "SELL"):
                    self._open(sig, price, i)
            else:
                should_close = (self.position["side"] == "long" and sig == "SELL") or \
                               (self.position["side"] == "short" and sig == "BUY")
                if should_close:
                    self._close(price, price, i, "信号平仓")

            self.equity_curve.append({"bar": i, "equity": self.capital})

        # 强制平仓
        if self.position:
            last_price = float(self.df["close"].iloc[-1])
            self._close(last_price, last_price, total - 1, "强制平仓")

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(self.capital, 2),
            "return_pct": round((self.capital / self.initial_capital - 1) * 100, 2),
            "trades": len(self.trades),
            "agent_calls": agent_calls,
            "tech_calls": tech_calls,
            "pnl_per_trade": round(sum(t["pnl"] for t in self.trades) / max(len(self.trades), 1), 4),
        }


async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="DOGE/USDT:USDT")
    p.add_argument("--tf", default="3m")
    p.add_argument("--mode", default="live")
    p.add_argument("--bars", type=int, default=100)
    p.add_argument("--capital", type=float, default=10)
    p.add_argument("--leverage", type=int, default=10)
    args = p.parse_args()

    df = load_data(args.symbol, args.tf, args.mode, args.bars)
    print(f"数据: {args.symbol} {args.tf}  {len(df)}根")
    print(f"范围: {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")
    print(f"参数: 本金${args.capital}  {args.leverage}x  仓位{80}%")

    # 构建 Agent
    print(f"\n初始化 1 Agent Solo ...")
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
    coordinator = AgentCoordinatorSolo()

    # 回测
    warmup = 50
    test_bars = max(0, len(df) - warmup)
    print(f"回测: warmup={warmup}  测试={test_bars}根  (约{test_bars * 3}分钟)")
    print(f"预计 {test_bars} 次 Agent 调用 ...")
    print()

    bt = AgentBacktest(df, capital=args.capital, leverage=args.leverage, warmup=warmup)

    t0 = datetime.now()
    result = await bt.run(coordinator)
    elapsed = (datetime.now() - t0).total_seconds()

    print(f"\n{'='*50}")
    print("Agent 回测结果")
    print(f"{'='*50}")
    print(f"初始资金: ${result['initial_capital']:.2f}")
    print(f"最终权益: ${result['final_equity']:.2f}")
    print(f"收益率:   {result['return_pct']}%")
    print(f"交易次数: {result['trades']}")
    print(f"Agent调用: {result['agent_calls']} 次")
    print(f"平均盈亏: ${result['pnl_per_trade']}")
    print(f"耗时:     {elapsed:.0f}s")

    # 保存
    name = args.symbol.split("/")[0].lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = RESULT_DIR / f"agent_{name}_{args.tf}_{ts}"
    subdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(bt.equity_curve).to_csv(subdir / "equity.csv", index=False)
    pd.DataFrame(bt.trades).to_csv(subdir / "trades.csv", index=False)
    (subdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n报告: {subdir}")


if __name__ == "__main__":
    asyncio.run(main())
