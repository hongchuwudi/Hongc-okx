"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_feedback.py 学习闭环盈亏百分比
描述: 钉住 generate_feedback 盈亏百分比公式用 OKX initialMargin，不再荒谬

回归背景: 旧公式 margin=entry*size*0.01 单位错误，真实 0.85% 盈亏被算成
+2539% 等荒谬值，污染 LLM 决策。现用 pnl/margin*100（margin=initialMargin）。

包含:
- class TestFeedbackProfitPct — 盈亏百分比公式正确性
- class TestFeedbackFormatting — 入场价精度与文案
"""
import pytest

from app.agents.toolkits.toolkit_data import load_data
from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback


# 真实 OKX 持仓快照（DOGE 多头，盈利）
_PROFIT_POS = {
    "side": "long", "size": 1.43, "entry_price": 0.0802,
    "unrealized_pnl": 0.0976, "margin": 11.46, "leverage": 10,
    "notional": 114.46, "mark_price": 0.0803,
}

# 真实 OKX 持仓快照（亏损）
_LOSS_POS = {
    "side": "short", "size": 1.43, "entry_price": 0.0802,
    "unrealized_pnl": -0.05, "margin": 11.46, "leverage": 10,
    "notional": 114.46, "mark_price": 0.0803,
}


# ═══════════════════════════════════════════════════════════════
# 盈亏百分比公式
# ═══════════════════════════════════════════════════════════════

class TestFeedbackProfitPct:
    """盈亏百分比必须接近真实值（~0.85%），不再荒谬。"""

    def test_profit_pct_uses_initial_margin(self):
        """盈利：pnl/margin*100 ≈ 0.85%，不是 +2539%。"""
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=_PROFIT_POS)
        feedback = generate_feedback()
        # 提取百分比
        assert "(+0.8%" in feedback or "(+0.9%" in feedback, (
            f"盈利百分比应 ~0.85%，实际: {feedback}"
        )
        # 绝不能出现荒谬的几千百分点
        assert "+25" not in feedback and "+253" not in feedback, (
            f"仍出现荒谬百分比: {feedback}"
        )

    def test_loss_pct_uses_initial_margin(self):
        """亏损：百分比合理（约 -0.44%），不是 -2185%。"""
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=_LOSS_POS)
        feedback = generate_feedback()
        assert "(-0.4%" in feedback or "(-0.5%" in feedback, (
            f"亏损百分比应 ~-0.44%，实际: {feedback}"
        )
        assert "-218" not in feedback, f"仍出现荒谬百分比: {feedback}"

    def test_margin_missing_falls_back_to_notional(self):
        """margin=0 时用 notional/leverage 兜底，百分比仍合理。"""
        pos = dict(_PROFIT_POS, margin=0)
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=pos)
        feedback = generate_feedback()
        # notional/leverage = 114.46/10 = 11.446，pct ≈ 0.85%
        assert "(+0.8%" in feedback or "(+0.9%" in feedback, (
            f"margin 缺失兜底应仍 ~0.85%，实际: {feedback}"
        )

    def test_margin_and_notional_zero_yields_zero_pct(self):
        """margin 和 notional 都为 0 时 pct=0，不产生荒谬值。"""
        pos = dict(_PROFIT_POS, margin=0, notional=0)
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=pos)
        feedback = generate_feedback()
        assert "(+0.0%)" in feedback, (
            f"margin/notional 全缺失应 pct=0，实际: {feedback}"
        )


# ═══════════════════════════════════════════════════════════════
# 入场价精度与文案
# ═══════════════════════════════════════════════════════════════

class TestFeedbackFormatting:
    """入场价显示精度 + 多空方向文案。"""

    def test_entry_price_shows_4_decimals_not_zero(self):
        """DOGE 价格 0.08 应显示 0.0802，不是 $0（旧 .0f 格式化 bug）。"""
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=_PROFIT_POS)
        feedback = generate_feedback()
        assert "@ $0.0802" in feedback, (
            f"入场价应显示 4 位小数 0.0802，实际: {feedback}"
        )
        assert "@ $0\n" not in feedback, "入场价不应被格式化成 $0"

    def test_long_direction_text(self):
        """多头持仓显示"多头"。"""
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=_PROFIT_POS)
        feedback = generate_feedback()
        assert "多头" in feedback

    def test_short_direction_text(self):
        """空头持仓显示"空头"。"""
        load_data(_df_stub(), price=0.0803, equity=10000.0, position=_LOSS_POS)
        feedback = generate_feedback()
        assert "空头" in feedback

    def test_no_position_holds(self):
        """无持仓时显示 HOLD 反馈。"""
        load_data(_df_stub(), price=0.0803, equity=10000.0, position={})
        feedback = generate_feedback()
        assert "HOLD" in feedback or "未开仓" in feedback


# 最小 DataFrame stub（generate_feedback 不读 df，但 load_data 需要）
def _df_stub():
    import pandas as pd
    return pd.DataFrame({"close": [0.08, 0.0801, 0.0803], "volume": [100, 100, 100]})
