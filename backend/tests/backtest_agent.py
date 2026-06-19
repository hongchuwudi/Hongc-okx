"""
Agent 回测 — 完整 loop 8 步流水线 + 真 Agent + 本地 K 线，模拟真实 tick

用法:
  python tests/backtest_agent.py
  python tests/backtest_agent.py --symbol DOGE/USDT:USDT --bars 200 --capital 10
"""

import sys, asyncio, json
from datetime import datetime
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
KLINE_DIR = ROOT / "data" / "kline"
RESULT_DIR = ROOT / "data" / "backtest"
RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ── 数据加载 ────────────────────────────────────────────

def load_csv(symbol: str, tf: str, mode: str, bars: int):
    name = symbol.split("/")[0].lower()
    files = sorted((KLINE_DIR / mode / name).glob(f"{name}_{tf}_*.csv"))
    if not files:
        raise FileNotFoundError(f"未找到 {symbol} {tf} ({mode})")
    df = pd.read_csv(files[-1])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.tail(bars).reset_index(drop=True)


# ── 模拟引擎 — 走完整 8 步流程 ──────────────────────────

class BacktestEngine:
    """逐 K 线模拟完整 tick 流程，用真 Agent + 本地数据。"""

    def __init__(self, df, capital=10, leverage=10, position_ratio=0.8, fee=0.001, warmup=50):
        self.df = df
        self.capital = capital  # 本金
        self.leverage = leverage
        self.position_ratio = position_ratio
        self.fee = fee
        self.warmup = warmup
        self.position = None  # 持仓: {side, size, entry_price, stop_loss, take_profit}
        self.trades = []
        self.equity_curve = []
        self.signals = []  # 记录每次 AI 信号

    # ── Step 2: 获取行情 ──
    def _fetch_market(self, i):
        bar = self.df.iloc[i]
        price = float(bar["close"])
        window = self.df.iloc[:i + 1]
        return window, price

    # ── Step 3: 策略分析 ──
    async def _analyze(self, window, price, coordinator):
        equity = max(self.capital, 1) * self.leverage
        return await coordinator.analyze(window, price, equity, self.position)

    # ── Step 4: 动态持仓管理 ──
    def _manage_position(self, price, signal):
        if not self.position:
            return signal
        # 盈利保护：盈利 > 5% 移动止损到保本
        pos = self.position
        entry = pos["entry_price"]
        if pos["side"] == "long":
            profit_pct = (price - entry) / entry * self.leverage * 100
            if profit_pct > 5:
                signal["stop_loss"] = max(signal.get("stop_loss", 0), entry * 1.01)
            elif profit_pct > 2:
                signal["stop_loss"] = max(signal.get("stop_loss", 0), price * 0.99)
        else:
            profit_pct = (entry - price) / entry * self.leverage * 100
            if profit_pct > 5:
                signal["stop_loss"] = min(signal.get("stop_loss", 0), entry * 0.99)
            elif profit_pct > 2:
                signal["stop_loss"] = min(signal.get("stop_loss", 0), price * 1.01)
        return signal

    # ── 止盈止损检查 ──
    def _check_stop(self, price, high, low):
        if not self.position:
            return None
        sl, tp = self.position["stop_loss"], self.position["take_profit"]
        side = self.position["side"]
        if side == "long":
            if low <= sl: return sl
            if high >= tp: return tp
        else:
            if high >= sl: return sl
            if low <= tp: return tp
        return None

    # ── Step 6: 风控检查 ──
    def _risk_check(self, signal):
        # 日亏损 > 本金 20% 停止
        loss = self.initial_capital - self.capital
        if loss > self.initial_capital * 0.2:
            return False, f"日亏损超限 ${loss:.2f}"
        # 连续 3 次 HOLD 后跳过
        return True, ""

    # ── Step 7: 执行交易 ──
    def _execute(self, signal, price, bar_idx):
        sig = signal["signal"]
        if sig == "HOLD":
            return

        if self.position is None:
            # 开仓
            if sig in ("BUY", "SELL"):
                trade_value = self.capital * self.leverage * self.position_ratio
                size = trade_value / price
                fee = size * price * self.fee
                self.capital -= fee
                self.position = {
                    "side": "long" if sig == "BUY" else "short",
                    "size": size, "entry_price": price,
                    "stop_loss": signal.get("stop_loss", price * 0.98),
                    "take_profit": signal.get("take_profit", price * 1.05),
                    "entry_bar": bar_idx, "entry_fee": fee,
                }
        else:
            # 平仓条件：反向信号
            should_close = (self.position["side"] == "long" and sig == "SELL") or \
                           (self.position["side"] == "short" and sig == "BUY")
            if should_close:
                self._close_position(price, bar_idx, "信号平仓")

    def _close_position(self, price, bar_idx, reason):
        pos = self.position
        size = pos["size"]
        fee = size * price * self.fee
        if pos["side"] == "long":
            pnl = (price - pos["entry_price"]) * size - fee - pos.get("entry_fee", 0)
        else:
            pnl = (pos["entry_price"] - price) * size - fee - pos.get("entry_fee", 0)
        self.capital += pnl + size * price - fee  # 归还本金 + PnL
        self.trades.append({
            "bar": bar_idx, "side": pos["side"], "entry": pos["entry_price"],
            "exit": price, "size": size, "pnl": round(pnl, 4),
            "bars_held": bar_idx - pos["entry_bar"], "reason": reason,
        })
        self.position = None

    # ── 主循环 ──
    async def run(self, coordinator):
        self.initial_capital = self.capital
        total = len(self.df)

        for i in range(self.warmup, total):
            bar = self.df.iloc[i]
            price = float(bar["close"])
            high = float(bar.get("high", price))
            low = float(bar.get("low", price))

            # Step 0: 止盈止损检查
            stopped = self._check_stop(price, high, low)
            if stopped:
                self._close_position(stopped, i, "TP/SL")
                self.equity_curve.append({"bar": i, "equity": round(self.capital, 2)})
                continue

            # Step 2: 获取行情
            window, price = self._fetch_market(i)

            # Step 3: Agent 分析
            try:
                decision = await self._analyze(window, price, coordinator)
                signal = {
                    "signal": decision.get("signal", "HOLD"),
                    "confidence": decision.get("confidence", "MEDIUM"),
                    "reason": decision.get("reason", ""),
                    "stop_loss": float(decision.get("stop_loss", price * 0.98)),
                    "take_profit": float(decision.get("take_profit", price * 1.05)),
                }
            except Exception as e:
                # 降级：技术指标
                from app.services.strategies.strategy_technical import TechnicalStrategy
                s = TechnicalStrategy()
                signal = s.generate_signal(window, self.position)

            # Step 4: 持仓管理
            signal = self._manage_position(price, signal)

            # Step 5: 记录信号
            self.signals.append({**signal, "bar": i, "price": price})

            # Step 6: 风控
            ok, reason = self._risk_check(signal)
            if not ok:
                print(f"  [风控拦截] {reason}")
                self.equity_curve.append({"bar": i, "equity": round(self.capital, 2)})
                continue

            # Step 7: 执行交易
            self._execute(signal, price, i)

            self.equity_curve.append({"bar": i, "equity": round(self.capital, 2)})

            # 进度
            if (i - self.warmup + 1) % 10 == 0:
                sig = signal["signal"]
                print(f"  bar {i}/{total} | ${price:.4f} | {sig:4s} | 权益 ${self.capital:.2f}")

        # 强制平仓
        if self.position:
            last_price = float(self.df["close"].iloc[-1])
            self._close_position(last_price, total - 1, "强制平仓")

        return self._report()

    def _report(self):
        total_pnl = sum(t["pnl"] for t in self.trades)
        wins = [t for t in self.trades if t["pnl"] > 0]
        losses = [t for t in self.trades if t["pnl"] <= 0]
        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(self.capital, 2),
            "return_pct": round((self.capital / self.initial_capital - 1) * 100, 2),
            "total_trades": len(self.trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / max(len(self.trades), 1) * 100, 1),
            "total_pnl": round(total_pnl, 4),
            "avg_win": round(sum(t["pnl"] for t in wins) / max(len(wins), 1), 4),
            "avg_loss": round(sum(t["pnl"] for t in losses) / max(len(losses), 1), 4),
            "profit_factor": round(abs(sum(t["pnl"] for t in wins) / max(sum(t["pnl"] for t in losses), 0.01)), 2),
            "signals": len(self.signals),
            "buy_signals": sum(1 for s in self.signals if s["signal"] == "BUY"),
            "sell_signals": sum(1 for s in self.signals if s["signal"] == "SELL"),
            "hold_signals": sum(1 for s in self.signals if s["signal"] == "HOLD"),
        }


# ── 入口 ───────────────────────────────────────────────

async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="DOGE/USDT:USDT")
    p.add_argument("--tf", default="3m")
    p.add_argument("--mode", default="live")
    p.add_argument("--bars", type=int, default=100)
    p.add_argument("--capital", type=float, default=10)
    p.add_argument("--leverage", type=int, default=10)
    p.add_argument("--pos-ratio", type=float, default=0.8)
    p.add_argument("--warmup", type=int, default=50)
    args = p.parse_args()

    df = load_csv(args.symbol, args.tf, args.mode, args.bars)
    test_bars = len(df) - args.warmup
    print(f"数据: {args.symbol} {args.tf}  {len(df)}根")
    print(f"范围: {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")
    print(f"参数: 本金${args.capital} {args.leverage}x 仓位{int(args.pos_ratio*100)}% warmup={args.warmup}")
    print(f"Agent 调用: {test_bars} 次 (预计 {test_bars * 15}s)\n")

    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
    coordinator = AgentCoordinatorSolo()

    engine = BacktestEngine(df, capital=args.capital, leverage=args.leverage,
                            position_ratio=args.pos_ratio, warmup=args.warmup)
    t0 = datetime.now()
    result = await engine.run(coordinator)
    elapsed = (datetime.now() - t0).total_seconds()

    print(f"\n{'='*50}")
    print("回测结果")
    print(f"{'='*50}")
    for k, v in result.items():
        print(f"  {k:20s}: {v}")

    # 保存
    name = args.symbol.split("/")[0].lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = RESULT_DIR / f"agent_{name}_{args.tf}_{ts}"
    subdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(engine.equity_curve).to_csv(subdir / "equity.csv", index=False)
    pd.DataFrame(engine.trades).to_csv(subdir / "trades.csv", index=False)
    pd.DataFrame(engine.signals).to_csv(subdir / "signals.csv", index=False)
    json.dump(result, (subdir / "result.json").open("w"), indent=2, ensure_ascii=False)
    print(f"\n报告 -> {subdir}")


if __name__ == "__main__":
    asyncio.run(main())
