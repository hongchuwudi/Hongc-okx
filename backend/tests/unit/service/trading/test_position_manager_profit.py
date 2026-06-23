"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_position_manager_profit.py 持仓管理盈亏百分比公式
描述: 钉住 PositionManager 用 OKX initialMargin 算盈亏百分比，不再荒谬

回归背景: 旧公式 margin=entry*size*0.01 单位错误，真实 0.85% 被算成 +2539%，
触发 _calc_trailing_stop 的 profit_pct>5 保本分支，导致 SL=TP=0.08（止盈止损失效）。
现用 pnl/margin*100（margin=initialMargin），真实小盈利不误触发保本。

包含:
- class TestProfitPctFormula — 盈亏百分比公式正确性
- class TestNoFalseTrailingStop — 真实小盈利不误触发保本移损
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.trading.position_manager import PositionManager


# 真实 OKX 持仓（多头小盈利，pnl/margin ≈ 0.85%）
_PROFIT_POS = {
    "side": "long", "size": 1.43, "entry_price": 0.0802,
    "unrealized_pnl": 0.0976, "margin": 11.46, "leverage": 10,
    "notional": 114.46, "mark_price": 0.0803,
}


def _make_pm():
    """构造 PositionManager 实例，exchange 为 mock。"""
    exchange = MagicMock()
    exchange.cancel_algo_orders = AsyncMock()
    exchange.create_algo_order = AsyncMock()
    return PositionManager(exchange, "DOGE/USDT:USDT")


# ═══════════════════════════════════════════════════════════════
# 盈亏百分比公式
# ═══════════════════════════════════════════════════════════════

class TestProfitPctFormula:
    """profit_pct 必须接近真实值（~0.85%），不触发 >2 / >5 保本分支。

    注意：TP 会因 ATR 自适应调整而更新（与 profit_pct 无关），所以不能断言
    updated=False。核心验证点是 SL 没被误拉到保本价 entry*1.01。
    """

    @pytest.mark.asyncio
    async def test_small_profit_does_not_trigger_breakeven(self):
        """真实小盈利 0.85% 时 SL 保持 current_sl，不跳到保本价 entry*1.01。

        旧公式会算成 +2539% 误触发 profit_pct>5 保本分支，SL 被移到 entry*1.01。
        新公式下 profit_pct≈0.85%，_calc_trailing_stop 返回 current_sl（保持）。
        """
        pm = _make_pm()
        result = await pm.update(
            position=_PROFIT_POS, current_price=0.0803, atr_pct=2.0,
            current_sl=0.0790, current_tp=0.0850,
        )
        # SL 保持 0.0790，不应被拉到 entry*1.01≈0.0810（保本+1%）
        assert abs(result["stop_loss"] - 0.0790) < 0.0001, (
            f"小盈利 SL 应保持 0.0790，实际 {result['stop_loss']}（误触发保本）"
        )

    @pytest.mark.asyncio
    async def test_margin_missing_falls_back_to_notional(self):
        """margin=0 时用 notional/leverage 兜底，SL 仍保持不误触发保本。"""
        pm = _make_pm()
        pos = dict(_PROFIT_POS, margin=0)
        result = await pm.update(
            position=pos, current_price=0.0803, atr_pct=2.0,
            current_sl=0.0790, current_tp=0.0850,
        )
        assert abs(result["stop_loss"] - 0.0790) < 0.0001, (
            f"margin 缺失兜底后 SL 应保持 0.0790，实际 {result['stop_loss']}"
        )

    @pytest.mark.asyncio
    async def test_margin_notional_zero_no_absurd_pct(self):
        """margin 和 notional 都为 0 时 pct=0，SL 保持不误触发保本。"""
        pm = _make_pm()
        pos = dict(_PROFIT_POS, margin=0, notional=0)
        result = await pm.update(
            position=pos, current_price=0.0803, atr_pct=2.0,
            current_sl=0.0790, current_tp=0.0850,
        )
        # pct=0 → 不触发保本，SL 保持
        assert abs(result["stop_loss"] - 0.0790) < 0.0001, (
            f"margin/notional 全缺失时 SL 应保持，实际 {result['stop_loss']}"
        )


# ═══════════════════════════════════════════════════════════════
# 不误触发保本移损
# ═══════════════════════════════════════════════════════════════

class TestNoFalseTrailingStop:
    """真实小盈利场景下 SL/TP 不被错误拉到保本价。"""

    @pytest.mark.asyncio
    async def test_sl_not_jumped_to_breakeven_on_small_profit(self):
        """SL 不应被拉到 entry*1.01（保本+1%）——那是 profit_pct>5 才该触发的。"""
        pm = _make_pm()
        result = await pm.update(
            position=_PROFIT_POS, current_price=0.0803, atr_pct=2.0,
            current_sl=0.0790, current_tp=0.0850,
        )
        # SL 保持 0.0790，不应变成 ~0.0810（entry*1.01）
        assert abs(result["stop_loss"] - 0.0790) < 0.0001, (
            f"SL 应保持 0.0790，实际 {result['stop_loss']}（可能误触发保本）"
        )

    @pytest.mark.asyncio
    async def test_large_profit_triggers_breakeven(self):
        """真大幅盈利（profit_pct>5）时才触发保本移损 —— 确认分支仍生效。"""
        pm = _make_pm()
        # 构造 profit_pct > 5：pnl=1.0, margin=11.46 → 8.7%
        pos = dict(_PROFIT_POS, unrealized_pnl=1.0)
        result = await pm.update(
            position=pos, current_price=0.0803, atr_pct=2.0,
            current_sl=0.0790, current_tp=0.0850,
        )
        # 大盈利触发保本 → SL 移到 entry*1.01=0.0810，updated=True
        assert result["updated"] is True, "大盈利应触发保本移损"
        assert abs(result["stop_loss"] - 0.0810) < 0.001, (
            f"保本 SL 应 ≈ 0.0810，实际 {result['stop_loss']}"
        )
