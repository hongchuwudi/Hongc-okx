"""
Created: 2026-06-14
Author: hongchuwudi
Description: 回测引擎计算正确性验证 — 用 Mock 策略逐笔验证开仓/持仓/平仓/强制平仓/指标

Contains:
- Function: test_open_close — 验证正常开平仓的资金计算
- Function: test_forced_close — 验证回测结束时强制平仓（本金必须归还）
- Function: test_equity_curve — 验证权益曲线初始点和每个点的值
- Function: test_metrics — 验证收益率/胜率/最大回撤等指标计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from typing import Dict, Optional

from app.strategies.base import BaseStrategy
from app.services.backtest.engine import run_backtest, run_backtest_stream


class MockStrategy(BaseStrategy):
    """预先设定信号的 Mock 策略，用于精确验证引擎计算"""

    @property
    def name(self) -> str:
        return "mock"

    def __init__(self, signals: dict):
        """
        signals: {bar_index: {"signal": "BUY", "confidence": "HIGH", ...}}
        未指定的 bar 默认返回 HOLD
        """
        self.signals = signals

    def generate_signal(self, df: pd.DataFrame, current_position: Optional[Dict] = None, **kwargs) -> Dict:
        bar = len(df) - 1
        if bar in self.signals:
            return self.signals[bar]
        return {"signal": "HOLD", "confidence": "LOW", "reason": "mock",
                "stop_loss": 90.0, "take_profit": 110.0}


def make_ohlcv(n_bars=60, base_price=100.0, step=0.5):
    """构造稳步上涨的 OHLCV 数据"""
    import numpy as np
    np.random.seed(42)
    data = []
    for i in range(n_bars):
        price = base_price + i * step
        data.append({
            "timestamp": pd.Timestamp("2026-06-14 00:00:00") + pd.Timedelta(hours=i),
            "open": price - step * np.random.uniform(0, 1),
            "high": price + step * 2,
            "low": price - step * 2,
            "close": price,
            "volume": np.random.uniform(100, 1000),
        })
    return pd.DataFrame(data)


# ============================================================
# 测试 1: 正常开仓 → 持仓 → 平仓的资金计算
# ============================================================
def test_open_close():
    """验证：开仓扣款 + 手续费，平仓归还本金 + 手续费，盈亏正确"""
    df = make_ohlcv(n_bars=60, base_price=100.0, step=0.5)
    initial_capital = 200.0
    position_ratio = 0.8
    fee_rate = 0.001

    # 设定信号：bar 52 BUY, bar 57 SELL
    mock = MockStrategy({
        52: {"signal": "BUY", "confidence": "HIGH", "reason": "mock_buy",
             "stop_loss": 90.0, "take_profit": 130.0},
        57: {"signal": "SELL", "confidence": "HIGH", "reason": "mock_sell",
             "stop_loss": 90.0, "take_profit": 130.0},
    })

    result = run_backtest(df, mock, initial_capital=initial_capital,
                          position_ratio=position_ratio, fee_rate=fee_rate, warmup=50)

    trades = result["trades"]
    equity = result["equity_curve"]
    metrics = result["metrics"]

    # -- 验证初始权益点 --
    assert equity[0]["equity"] == initial_capital, \
        f"初始权益应={initial_capital}，实际={equity[0]['equity']}"

    # -- 验证交易数量 --
    assert len(trades) == 1, f"应有 1 笔交易，实际 {len(trades)} 笔"

    t = trades[0]
    bar_52_price = 100.0 + 52 * 0.5     # 126.0
    bar_57_price = 100.0 + 57 * 0.5     # 128.5

    # -- 验证入场价 --
    assert abs(t["entry"] - bar_52_price) < 0.01, \
        f"入场价应为 {bar_52_price}，实际 {t['entry']}"

    # -- 验证出场价 --
    assert abs(t["exit"] - bar_57_price) < 0.01, \
        f"出场价应为 {bar_57_price}，实际 {t['exit']}"

    # -- 验证开仓数量 --
    trade_capital = initial_capital * position_ratio  # 160
    entry_fee = trade_capital * fee_rate               # 0.16
    expected_size = trade_capital / bar_52_price       # 160 / 126 = 1.2698...
    assert abs(t["size"] - expected_size) < 0.0001, \
        f"仓位应为 {expected_size:.6f}，实际 {t['size']:.6f}"

    # -- 验证盈亏（含开仓费 + 平仓费） --
    gross_pnl = (bar_57_price - bar_52_price) * expected_size   # 2.5 * 1.2698 = 3.1746
    exit_fee = t["size"] * bar_57_price * fee_rate               # 1.2698 * 128.5 * 0.001 = 0.1632
    expected_pnl = gross_pnl - exit_fee - entry_fee               # 3.1746 - 0.1632 - 0.16 = 2.8514
    assert abs(t["pnl"] - round(expected_pnl, 4)) < 0.01, \
        f"盈亏应为 {expected_pnl:.4f}，实际 {t['pnl']:.4f}"

    # -- 验证最终权益 --
    expected_final = initial_capital - entry_fee + gross_pnl - exit_fee  # 200 - 0.16 + 3.1746 - 0.1632 = 202.8514
    final_equity = equity[-1]["equity"]
    assert abs(final_equity - round(expected_final, 2)) < 0.1, \
        f"最终权益应为 {expected_final:.2f}，实际 {final_equity}"

    # -- 验证指标 --
    assert metrics["total_trades"] == 1
    assert metrics["winning_trades"] == 1
    assert metrics["losing_trades"] == 0
    assert metrics["win_rate"] == 100.0
    assert metrics["profit_factor"] == 999.99  # cap value when 0 losses
    assert metrics["total_return_pct"] > 0, "盈利交易应对应正收益"

    print("[PASS] test_open_close")


# ============================================================
# 测试 2: 强制平仓时本金必须归还
# ============================================================
def test_forced_close():
    """验证：回测结束时若有持仓，本金必须归还（修复后不应再出现 -79% 的假亏损）"""
    df = make_ohlcv(n_bars=60, base_price=100.0, step=0.5)
    initial_capital = 200.0
    position_ratio = 0.8
    fee_rate = 0.001

    # 只 BUY 不平仓，让回测结束时强制平仓
    mock = MockStrategy({
        52: {"signal": "BUY", "confidence": "HIGH", "reason": "mock_buy",
             "stop_loss": 90.0, "take_profit": 200.0},
    })

    result = run_backtest(df, mock, initial_capital=initial_capital,
                          position_ratio=position_ratio, fee_rate=fee_rate, warmup=50)

    trades = result["trades"]
    equity = result["equity_curve"]

    # 应该有一笔 FORCED_CLOSE 交易
    assert len(trades) == 1, f"应有 1 笔强制平仓，实际 {len(trades)} 笔"
    assert trades[0]["confidence"] == "FORCED_CLOSE", "最后一笔应为强制平仓"

    final_equity = equity[-1]["equity"]
    # 强制平仓后权益应接近初始本金（价格微涨 + 扣除两次手续费）
    assert final_equity > initial_capital * 0.95, \
        f"强制平仓后权益 {final_equity} 不应远低于本金 {initial_capital}（本金必须归还）"

    # 开仓时扣除的仓位资金应该在最终权益中体现
    trade_capital = initial_capital * position_ratio  # 160
    # 权益应 > 剩余现金（初始-开仓资金），否则说明仓位资金没归还
    remaining_cash = initial_capital - trade_capital - trade_capital * fee_rate
    assert final_equity > remaining_cash + trade_capital * 0.99, \
        f"强制平仓后权益 {final_equity} 应包含归还的持仓市值 (~{trade_capital})，而不只是现金 {remaining_cash:.2f}"

    print("[PASS] test_forced_close")


# ============================================================
# 测试 3: 权益曲线连续性
# ============================================================
def test_equity_curve():
    """验证：权益曲线包含初始点，开仓后立即反映 unrealized PnL"""
    df = make_ohlcv(n_bars=60, base_price=100.0, step=0.5)
    mock = MockStrategy({
        52: {"signal": "BUY", "confidence": "HIGH", "reason": "mock_buy",
             "stop_loss": 90.0, "take_profit": 200.0},
    })

    result = run_backtest(df, mock, initial_capital=200.0, position_ratio=0.8,
                          fee_rate=0.001, warmup=50)
    equity = result["equity_curve"]

    # 第一点应为初始权益
    assert equity[0]["equity"] == 200.0, \
        f"权益曲线第一点应为初始本金 200.0，实际 {equity[0]['equity']}"

    # 开仓前（bar 50-51 无信号）权益不变，仍为初始值
    # 开仓后（bar 52 BUY）权益因手续费下降
    assert equity[0]["equity"] == equity[1]["equity"] == equity[2]["equity"] == 200.0, \
        "开仓前权益应保持不变"
    assert equity[3]["equity"] < 200.0, \
        "开仓后权益应因手续费下降"

    # 最后一点（强制平仓后追加）应回升到接近初始本金
    assert equity[-1]["equity"] > 190.0, \
        f"强制平仓归还本金后权益应接近初始值，实际 {equity[-1]['equity']}"

    print("[PASS] test_equity_curve")


# ============================================================
# 测试 4: 流式版与批量版结果一致
# ============================================================
def test_stream_consistency():
    """验证：run_backtest_stream 最终 done 事件与 run_backtest 返回完全一致"""
    df = make_ohlcv(n_bars=60, base_price=100.0, step=0.5)
    mock = MockStrategy({
        52: {"signal": "BUY", "confidence": "HIGH", "reason": "mock_buy",
             "stop_loss": 90.0, "take_profit": 130.0},
        57: {"signal": "SELL", "confidence": "HIGH", "reason": "mock_sell",
             "stop_loss": 90.0, "take_profit": 130.0},
    })

    # 批量版
    batch = run_backtest(df, mock, initial_capital=200.0, position_ratio=0.8,
                         fee_rate=0.001, warmup=50)

    # 流式版 — 收集所有事件
    stream_events = list(run_backtest_stream(df, mock, initial_capital=200.0,
                                              position_ratio=0.8, fee_rate=0.001, warmup=50))
    done_event = stream_events[-1]

    assert done_event["type"] == "done"
    # 指标一致
    for k in batch["metrics"]:
        assert abs(batch["metrics"][k] - done_event["metrics"][k]) < 0.01, \
            f"指标 {k} 不一致: 批量={batch['metrics'][k]}, 流式={done_event['metrics'][k]}"

    # 交易一致
    assert len(batch["trades"]) == len(done_event["trades"]), \
        f"交易数量不一致: 批量={len(batch['trades'])}, 流式={len(done_event['trades'])}"

    # 权益曲线一致
    assert len(batch["equity_curve"]) == len(done_event["equity_curve"]), \
        f"权益曲线长度不一致: 批量={len(batch['equity_curve'])}, 流式={len(done_event['equity_curve'])}"

    print("[PASS] test_stream_consistency")


# ============================================================
# 测试 5: 最大回撤计算
# ============================================================
def test_max_drawdown():
    """验证：最大回撤反映完整的资金变化（含初始→开仓的下跌）"""
    df = make_ohlcv(n_bars=60, base_price=100.0, step=-0.5)  # 持续下跌
    mock = MockStrategy({
        52: {"signal": "BUY", "confidence": "HIGH", "reason": "mock_buy",
             "stop_loss": 60.0, "take_profit": 120.0},
    })

    result = run_backtest(df, mock, initial_capital=200.0, position_ratio=0.8,
                          fee_rate=0.001, warmup=50)
    metrics = result["metrics"]

    # 持续下跌 + 多头持仓，最大回撤应 > 0
    assert metrics["max_drawdown_pct"] > 0, \
        f"持续下跌时应存在回撤，实际 max_drawdown={metrics['max_drawdown_pct']}%"

    # 回撤应该包含初始本金全额（而不是只从开仓后算起）
    assert metrics["max_drawdown_pct"] > 0.05, \
        f"手续费 + 跌幅应导致 > 0.05% 回撤，实际 {metrics['max_drawdown_pct']}%"

    print(f"[PASS] test_max_drawdown (max_drawdown={metrics['max_drawdown_pct']}%)")


# ============================================================
# 测试 6: 多次交易场景
# ============================================================
def test_multiple_trades():
    """验证：多次开平仓时交易记录和权益计算正确"""
    df = make_ohlcv(n_bars=60, base_price=100.0, step=0.3)
    mock = MockStrategy({
        51: {"signal": "BUY", "confidence": "HIGH", "reason": "trade1_buy",
             "stop_loss": 90.0, "take_profit": 120.0},
        54: {"signal": "SELL", "confidence": "HIGH", "reason": "trade1_sell",
             "stop_loss": 90.0, "take_profit": 120.0},
        55: {"signal": "SELL", "confidence": "HIGH", "reason": "trade2_short",
             "stop_loss": 130.0, "take_profit": 90.0},
        58: {"signal": "BUY", "confidence": "HIGH", "reason": "trade2_cover",
             "stop_loss": 130.0, "take_profit": 90.0},
    })

    result = run_backtest(df, mock, initial_capital=200.0, position_ratio=0.8,
                          fee_rate=0.001, warmup=50)
    trades = result["trades"]
    metrics = result["metrics"]

    assert len(trades) == 2, f"应有 2 笔交易，实际 {len(trades)} 笔"
    # 第一笔多，第二笔空
    assert trades[0]["side"] == "long", f"第一笔应为多头，实际 {trades[0]['side']}"
    assert trades[1]["side"] == "short", f"第二笔应为空头，实际 {trades[1]['side']}"
    assert metrics["total_trades"] == 2
    print(f"[PASS] test_multiple_trades (win_rate={metrics['win_rate']}%)")


if __name__ == "__main__":
    print("=" * 60)
    print("Backtest Engine Calculation Verification")
    print("=" * 60)
    test_open_close()
    test_forced_close()
    test_equity_curve()
    test_stream_consistency()
    test_max_drawdown()
    test_multiple_trades()
    print("=" * 60)
    print("All 6 tests passed")
    print("=" * 60)
