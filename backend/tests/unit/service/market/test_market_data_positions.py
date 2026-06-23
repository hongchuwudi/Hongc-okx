"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_market_data_positions.py 持仓解析字段归一化
描述: 钉住 get_positions 字段处理 — pnl_pct 不 ×100、side 规范化、entry 兜底

回归背景:
- 旧 pnl_pct = percentage * 100，ccxt percentage 已是百分数（1.6455=1.6455%），
  ×100 算成 164.55%，污染盈亏显示
- side 直接透传 ccxt 值，可能为 None/空，下游索引报错

包含:
- class TestPnlPctNotDoubled — pnl_pct 不再 ×100
- class TestSideNormalization — side 规范化为 long/short/None
- class TestEntryPriceFallback — entryPrice=0 时 markPrice 兜底
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.market.market_data import MarketDataService


def _ccxt_pos(**overrides) -> dict:
    """构造一个 ccxt fetch_positions 返回的持仓 dict。"""
    base = {
        "symbol": "DOGE/USDT:USDT",
        "side": "long",
        "contracts": 1.43,
        "entryPrice": 0.0802,
        "markPrice": 0.0803,
        "unrealizedPnl": 0.0976,
        "percentage": 1.6455,  # ccxt 已是百分数
        "leverage": 10,
        "initialMargin": 11.46,
        "notional": 114.46,
        "liquidationPrice": 0.072,
    }
    base.update(overrides)
    return base


def _make_service(positions: list) -> MarketDataService:
    """构造 MarketDataService，fetch_positions 返回指定持仓列表。"""
    exchange = MagicMock()
    exchange.fetch_positions = AsyncMock(return_value=positions)
    return MarketDataService(exchange)


# ═══════════════════════════════════════════════════════════════
# pnl_pct 不 ×100
# ═══════════════════════════════════════════════════════════════

class TestPnlPctNotDoubled:
    """pnl_pct 应等于 ccxt percentage 原值，不再 ×100。"""

    @pytest.mark.asyncio
    async def test_pnl_pct_equals_percentage_raw(self):
        """percentage=1.6455 → pnl_pct=1.6455，不是 164.55。"""
        svc = _make_service([_ccxt_pos(percentage=1.6455)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["pnl_pct"] == pytest.approx(1.6455, abs=0.001), (
            f"pnl_pct 应为 1.6455，实际 {pos['pnl_pct']}"
        )

    @pytest.mark.asyncio
    async def test_pnl_pct_negative(self):
        """负百分比保留负号。"""
        svc = _make_service([_ccxt_pos(percentage=-0.85)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["pnl_pct"] == pytest.approx(-0.85, abs=0.01)

    @pytest.mark.asyncio
    async def test_pnl_pct_none_yields_zero(self):
        """percentage 为 None 时 pnl_pct=0。"""
        svc = _make_service([_ccxt_pos(percentage=None)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["pnl_pct"] == 0


# ═══════════════════════════════════════════════════════════════
# side 规范化
# ═══════════════════════════════════════════════════════════════

class TestSideNormalization:
    """side 规范化为 long/short/None，非法值不透传。"""

    @pytest.mark.asyncio
    async def test_side_long_preserved(self):
        svc = _make_service([_ccxt_pos(side="long")])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["side"] == "long"

    @pytest.mark.asyncio
    async def test_side_short_preserved(self):
        svc = _make_service([_ccxt_pos(side="short")])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["side"] == "short"

    @pytest.mark.asyncio
    async def test_side_none_normalized(self):
        """side=None 时规范化为 None，不透传脏值。"""
        svc = _make_service([_ccxt_pos(side=None)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["side"] is None

    @pytest.mark.asyncio
    async def test_side_empty_string_normalized(self):
        """side='' 时规范化为 None。"""
        svc = _make_service([_ccxt_pos(side="")])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["side"] is None


# ═══════════════════════════════════════════════════════════════
# entryPrice 兜底
# ═══════════════════════════════════════════════════════════════

class TestEntryPriceFallback:
    """entryPrice=0 时用 markPrice 兜底。"""

    @pytest.mark.asyncio
    async def test_entry_zero_falls_back_to_mark(self):
        """entryPrice=0，markPrice>0 → entry=markPrice。"""
        svc = _make_service([_ccxt_pos(entryPrice=0.0, markPrice=0.0803)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["entry_price"] == pytest.approx(0.0803, abs=0.0001)

    @pytest.mark.asyncio
    async def test_entry_none_falls_back_to_mark(self):
        """entryPrice=None → 用 markPrice。"""
        svc = _make_service([_ccxt_pos(entryPrice=None, markPrice=0.0805)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["entry_price"] == pytest.approx(0.0805, abs=0.0001)

    @pytest.mark.asyncio
    async def test_entry_and_mark_both_zero(self):
        """entryPrice=0 且 markPrice=0 → entry=0（下游 feedback/PM 再用现价兜底）。"""
        svc = _make_service([_ccxt_pos(entryPrice=0.0, markPrice=0.0)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos["entry_price"] == 0.0


# ═══════════════════════════════════════════════════════════════
# 无持仓
# ═══════════════════════════════════════════════════════════════

class TestNoPosition:
    """无持仓（contracts=0）返回 None。"""

    @pytest.mark.asyncio
    async def test_zero_contracts_returns_none(self):
        svc = _make_service([_ccxt_pos(contracts=0)])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos is None

    @pytest.mark.asyncio
    async def test_empty_positions_returns_none(self):
        svc = _make_service([])
        pos = await svc.get_positions("DOGE/USDT:USDT")
        assert pos is None
