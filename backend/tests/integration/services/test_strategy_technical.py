"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_strategy_technical.py 技术指标策略集成测试
描述: 真实 K 线 → IndicatorService.calculate_all → 5 信号打分 → 决策完整链路

不依赖 LLM，纯计算层 + 指标服务，可稳定跑通。
用 data/kline 真实 K 线 + 构造走势段验证三种信号路径。

验证契约（确定不变，不预设特定走势必须出特定信号）:
- generate_signal 返回 dict 含 signal/confidence/reason/stop_loss/take_profit
- signal ∈ {BUY, SELL, HOLD}
- confidence ∈ {HIGH, MEDIUM, LOW}
- stop_loss/take_profit > 0
- BUY: stop_loss < take_profit；SELL: stop_loss > take_profit
- IndicatorService.calculate_all 补全 rsi/macd/sma/atr 等列

包含:
- class TestStrategyOutputContract — 输出结构契约（多币种真实 K 线）
- class TestIndicatorServiceIntegration — 指标服务补全列契约
- class TestSignalDirectionConsistency — 信号方向与 SL/TP 一致性
- class TestConstructedTrends — 构造走势段覆盖 BUY/SELL/HOLD 路径
"""
import numpy as np
import pandas as pd
import pytest

from app.agents.indicator import IndicatorService
from app.services.strategies.strategy_technical import TechnicalStrategy


_VALID_SIGNALS = {"BUY", "SELL", "HOLD"}
_VALID_CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}

# 多币种真实 K 线路径，覆盖不同标的
_REAL_KLINES = [
    "data/kline/demo/doge/doge_3m_2026-06-18_073000_2026-06-22_112700.csv",
    "data/kline/demo/ada/ada_1h_2026-03-31_040000_2026-06-22_110000.csv",
    "data/kline/demo/avax/avax_15m_2026-06-01_154500_2026-06-22_113000.csv",
]


# ═══════════════════════════════════════════════════════════════
# 数据加载辅助
# ═══════════════════════════════════════════════════════════════

def _load_kline(path: str, n_rows: int = 200) -> pd.DataFrame:
    """加载真实 K 线，取末尾 n_rows 根，timestamp 设为索引。"""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df.tail(n_rows).copy()


def _constructed_trend(direction: str, n: int = 200, seed: int = 1) -> pd.DataFrame:
    """构造指定方向的走势段（温和斜率 + 噪声），避免触发 RSI 极值修正。

    direction: "up" / "down" / "sideways"
    """
    rng = np.random.RandomState(seed)
    idx = pd.date_range("2026-06-01", periods=n, freq="3min")
    if direction == "up":
        close = np.linspace(0.50, 0.80, n) + rng.randn(n) * 0.006
    elif direction == "down":
        close = np.linspace(1.00, 0.82, n) + rng.randn(n) * 0.01
    else:
        close = 0.70 + rng.randn(n) * 0.002
    return pd.DataFrame({
        "open": close + 0.002,
        "high": close + 0.005,
        "low": close - 0.005,
        "close": close,
        "volume": rng.rand(n) * 1000 + 500,
    }, index=idx)


# ═══════════════════════════════════════════════════════════════
# 输出结构契约
# ═══════════════════════════════════════════════════════════════

class TestStrategyOutputContract:
    """多币种真实 K 线下，generate_signal 输出结构必须完整且合法。"""

    @pytest.fixture
    def strategy(self):
        return TechnicalStrategy()

    @pytest.fixture(params=_REAL_KLINES)
    def real_result(self, request, strategy):
        """每种币种真实 K 线跑一次策略。"""
        df = _load_kline(request.param)
        return strategy.generate_signal(df)

    def test_returns_dict(self, real_result):
        assert isinstance(real_result, dict), f"应为 dict，实际 {type(real_result)}"

    def test_has_all_required_keys(self, real_result):
        for key in ("signal", "confidence", "reason", "stop_loss", "take_profit"):
            assert key in real_result, f"缺少 key: {key}"

    def test_signal_is_valid(self, real_result):
        assert real_result["signal"] in _VALID_SIGNALS, (
            f"signal={real_result['signal']} 不在合法集合"
        )

    def test_confidence_is_valid(self, real_result):
        assert real_result["confidence"] in _VALID_CONFIDENCE, (
            f"confidence={real_result['confidence']} 不在合法集合"
        )

    def test_reason_is_nonempty_string(self, real_result):
        assert isinstance(real_result["reason"], str) and len(real_result["reason"]) > 0

    def test_sl_tp_positive(self, real_result):
        sl, tp = float(real_result["stop_loss"]), float(real_result["take_profit"])
        assert sl > 0 and tp > 0, f"sl={sl} tp={tp} 应为正数"


# ═══════════════════════════════════════════════════════════════
# 指标服务集成
# ═══════════════════════════════════════════════════════════════

class TestIndicatorServiceIntegration:
    """IndicatorService.calculate_all 补全指标列，是策略链路的真实前置。"""

    @pytest.fixture
    def enriched_df(self):
        df = _load_kline(_REAL_KLINES[0])
        return IndicatorService.calculate_all(df)

    def test_calculate_all_preserves_row_count(self, enriched_df):
        assert len(enriched_df) == 200, f"行数应保持 200，实际 {len(enriched_df)}"

    def test_calculate_all_adds_rsi(self, enriched_df):
        assert "rsi" in enriched_df.columns, "应补全 rsi 列"
        assert not enriched_df["rsi"].isna().all(), "rsi 列不应全为 NaN"

    def test_calculate_all_adds_macd(self, enriched_df):
        assert "macd" in enriched_df.columns, "应补全 macd 列"
        assert "macd_signal" in enriched_df.columns, "应补全 macd_signal 列"

    def test_calculate_all_adds_sma(self, enriched_df):
        assert "sma_20" in enriched_df.columns, "应补全 sma_20 列"
        assert "sma_50" in enriched_df.columns, "应补全 sma_50 列"

    def test_atr_pct_returns_positive(self, enriched_df):
        atr = IndicatorService.atr_pct(enriched_df)
        assert isinstance(atr, (int, float)) and atr > 0, f"atr_pct={atr} 应为正数"


# ═══════════════════════════════════════════════════════════════
# 信号方向与 SL/TP 一致性
# ═══════════════════════════════════════════════════════════════

class TestSignalDirectionConsistency:
    """SL/TP 必须在现价正确一侧，与信号方向一致（防参数传反 bug）。"""

    @pytest.fixture
    def strategy(self):
        return TechnicalStrategy()

    @pytest.fixture(params=_REAL_KLINES)
    def pair(self, request, strategy):
        """(result, latest_price) 配对，用于方向一致性断言。"""
        df = _load_kline(request.param)
        result = strategy.generate_signal(df)
        price = float(df["close"].iloc[-1])
        return result, price

    def test_buy_sl_below_tp(self, pair):
        result, _ = pair
        if result["signal"] != "BUY":
            pytest.skip("非 BUY 信号")
        sl, tp = float(result["stop_loss"]), float(result["take_profit"])
        assert sl < tp, f"BUY: sl({sl}) 应 < tp({tp})"

    def test_sell_sl_above_tp(self, pair):
        result, _ = pair
        if result["signal"] != "SELL":
            pytest.skip("非 SELL 信号")
        sl, tp = float(result["stop_loss"]), float(result["take_profit"])
        assert sl > tp, f"SELL: sl({sl}) 应 > tp({tp})"

    def test_buy_sl_below_current_price(self, pair):
        """BUY 止损应在现价之下（买入后价格跌破才止损）。"""
        result, price = pair
        if result["signal"] != "BUY":
            pytest.skip("非 BUY 信号")
        assert float(result["stop_loss"]) < price, (
            f"BUY: sl({result['stop_loss']}) 应 < 现价({price})"
        )

    def test_sell_sl_above_current_price(self, pair):
        """SELL 止损应在现价之上（卖出后价格涨破才止损）。"""
        result, price = pair
        if result["signal"] != "SELL":
            pytest.skip("非 SELL 信号")
        assert float(result["stop_loss"]) > price, (
            f"SELL: sl({result['stop_loss']}) 应 > 现价({price})"
        )


# ═══════════════════════════════════════════════════════════════
# 构造走势段覆盖三种信号路径
# ═══════════════════════════════════════════════════════════════

class TestConstructedTrends:
    """构造走势段，确保 BUY/SELL/HOLD 三条路径都被真实执行过。"""

    @pytest.fixture
    def strategy(self):
        return TechnicalStrategy()

    def test_uptrend_can_produce_buy(self, strategy):
        """温和上涨段至少有一种种子能产出 BUY（覆盖 BUY 路径）。"""
        signals = []
        for seed in range(5):
            df = _constructed_trend("up", seed=seed)
            signals.append(strategy.generate_signal(df)["signal"])
        assert "BUY" in signals, f"上涨段未产出 BUY，实际 {signals}"

    def test_downtrend_can_produce_sell(self, strategy):
        """温和下跌段至少有一种种子能产出 SELL（覆盖 SELL 路径）。"""
        signals = []
        for seed in range(5):
            df = _constructed_trend("down", seed=seed)
            signals.append(strategy.generate_signal(df)["signal"])
        assert "SELL" in signals, f"下跌段未产出 SELL，实际 {signals}"

    def test_sideways_produces_hold(self, strategy):
        """窄幅震荡段应产出 HOLD（覆盖 HOLD 路径）。"""
        df = _constructed_trend("sideways", seed=3)
        result = strategy.generate_signal(df)
        assert result["signal"] == "HOLD", (
            f"震荡段应 HOLD，实际 {result['signal']}"
        )

    def test_all_constructed_outputs_valid(self, strategy):
        """所有构造段的输出都必须满足结构契约。"""
        for direction in ("up", "down", "sideways"):
            for seed in range(3):
                df = _constructed_trend(direction, seed=seed)
                r = strategy.generate_signal(df)
                assert r["signal"] in _VALID_SIGNALS, f"{direction}/{seed}: {r['signal']}"
                assert r["confidence"] in _VALID_CONFIDENCE
                assert float(r["stop_loss"]) > 0 and float(r["take_profit"]) > 0
