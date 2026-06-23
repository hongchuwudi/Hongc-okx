"""
测试: 1 Agent Solo 的 _base() 方法 —— 构建预计算上下文
"""

from contextlib import ExitStack
from unittest.mock import patch, MagicMock


def test_base_returns_required_keys(sample_df):
    """_base() 必须返回 messages / remaining_steps / price / equity。"""
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
    with patch.object(AgentCoordinatorSolo, '__init__', lambda self: None):
        coordinator = AgentCoordinatorSolo.__new__(AgentCoordinatorSolo)
        coordinator._agent = MagicMock()
        coordinator._llm = MagicMock()
        coordinator._logger = MagicMock()

        with ExitStack() as stack:
            for ctx in _patches(sample_df):
                stack.enter_context(ctx)
            base = coordinator._base(100.0, 10000.0, sample_df)

    assert "messages" in base
    assert base["remaining_steps"] == 6
    assert base["price"] == 100.0
    assert base["equity"] == 10000.0


def test_base_context_contains_indicators(sample_df):
    """上下文文本含 RSI/MACD/SMA/布林带/ATR。"""
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
    with patch.object(AgentCoordinatorSolo, '__init__', lambda self: None):
        coordinator = AgentCoordinatorSolo.__new__(AgentCoordinatorSolo)
        coordinator._agent = MagicMock()
        coordinator._llm = MagicMock()
        coordinator._logger = MagicMock()

        with ExitStack() as stack:
            for ctx in _patches(sample_df):
                stack.enter_context(ctx)
            base = coordinator._base(100.0, 10000.0, sample_df)

    context = base["messages"][0].content
    assert "RSI" in context
    assert "MACD" in context
    assert "SMA20" in context
    assert "布林带" in context
    assert "ATR" in context


def test_base_with_position(sample_df):
    """有持仓时上下文显示多头/入场价。"""
    from app.agents.coordinators.coordinator_solo import AgentCoordinatorSolo
    with patch.object(AgentCoordinatorSolo, '__init__', lambda self: None):
        coordinator = AgentCoordinatorSolo.__new__(AgentCoordinatorSolo)
        coordinator._agent = MagicMock()
        coordinator._llm = MagicMock()
        coordinator._logger = MagicMock()

        with ExitStack() as stack:
            for ctx in _patches(sample_df, has_position=True):
                stack.enter_context(ctx)
            base = coordinator._base(100.0, 10000.0, sample_df)

    context = base["messages"][0].content
    assert "多头" in context
    assert "95.0" in context


def _patches(sample_df, has_position=False):
    """构建 IndicatorService 的 mock 上下文列表。"""
    pos = {"side": "long", "size": 0.5, "entry_price": 95.0,
           "unrealized_pnl": 250.0, "leverage": 10} if has_position else None
    return [
        patch('app.agents.coordinators.coordinator_solo.load_data'),
        patch('app.agents.coordinators.coordinator_solo._position', return_value=pos),
        patch('app.agents.coordinators.coordinator_solo.evaluate_position_risk', return_value="mock"),
        patch('app.agents.coordinators.coordinator_solo.calc_max_position', return_value="50张"),
        patch('app.agents.coordinators.coordinator_solo.calc_sl_tp', return_value="SL=97 TP=105"),
        patch('app.agents.coordinators.coordinator_solo.get_runtime', return_value=10),
        patch('app.agents.coordinators.coordinator_solo.IndicatorService.latest_indicators', return_value={
            "sma_5": 100.0, "sma_20": 99.0, "sma_50": 95.0,
            "rsi": 55.0, "macd": 0.5, "macd_signal": 0.3,
            "macd_histogram": 0.2, "bb_upper": 105.0, "bb_lower": 95.0,
            "bb_position": 0.5, "volume_ratio": 1.2,
        }),
        patch('app.agents.coordinators.coordinator_solo.IndicatorService.atr_pct', return_value=2.0),
        patch('app.agents.coordinators.coordinator_solo.IndicatorService.calc_rsi', return_value=55.0),
        patch('app.agents.coordinators.coordinator_solo.IndicatorService.trend_analysis', return_value={
            "short_term": "上涨", "medium_term": "上涨",
            "macd": "bullish", "overall": "强势上涨", "rsi_level": 55.0,
        }),
    ]
