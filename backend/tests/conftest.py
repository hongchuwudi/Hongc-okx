"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: conftest.py 全局测试夹具
描述: 共享测试夹具 — 模拟行情数据 + Mock 引擎对象

包含:
- fixture: sample_df — 60 行模拟 K 线（engine 测试用，含 open 列）
- fixture: sample_account — 模拟账户
- fixture: sample_position — 模拟多头持仓
- fixture: mock_engine — Mock 引擎对象（覆盖所有外部依赖）
- fixture: sample_ohlcv — 200 行模拟 K 线（toolkits 测试用）
- fixture: load_fixtures — 将数据注入 toolkits.toolkit_data
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.trading.strategy import AggregatedSignal
from app.services.risk.risk import RiskResult


# ── Engine 测试夹具（60 行，含 open 列）────────────────────────

@pytest.fixture
def sample_df():
    """60 行模拟 OHLCV 数据，稳步上涨趋势。"""
    np.random.seed(42)
    n = 60
    close = np.cumsum(np.random.randn(n) * 2) + 100
    return pd.DataFrame({
        "close": close,
        "high": close + abs(np.random.randn(n) * 0.5),
        "low": close - abs(np.random.randn(n) * 0.5),
        "open": close - np.random.randn(n) * 0.3,
        "volume": np.random.rand(n) * 1000 + 500,
    })


@pytest.fixture
def sample_account():
    """模拟账户信息，结构与 MarketDataService.get_account_info 一致。"""
    return {"balance": 9000.0, "equity": 10000.0, "leverage": 1}


@pytest.fixture
def sample_position():
    """模拟多头持仓，结构与 MarketDataService.get_positions 一致。"""
    return {
        "side": "long", "size": 0.1, "entry_price": 95.0,
        "unrealized_pnl": 50.0, "leverage": 1, "mark_price": 100.0,
        "margin": 9.5, "notional": 10.0, "pnl_pct": 5.0,
        "liquidation_price": 1.0,
    }


@pytest.fixture
def mock_engine(sample_df, sample_account):
    """Mock 引擎对象，所有外部依赖均为 AsyncMock/MagicMock。

    测试中通过 engine.xxx.return_value = ... 覆盖特定返回值。
    """
    engine = MagicMock()
    engine._symbol = "DOGE/USDT:USDT"
    engine._probe_count = 0
    engine._agent_fail_count = 0
    engine.use_multi_agent = True
    engine.agent_mode_display = "5 Agent Swarm"
    engine._open_trade_memory_id = None

    engine.exchange = MagicMock()
    engine.exchange.use_backup = False
    engine.exchange.switch_to_primary = MagicMock()
    engine.exchange.switch_to_backup = MagicMock(return_value=True)

    engine.market_data = MagicMock()
    engine.market_data.get_ohlcv = AsyncMock(return_value=sample_df)
    engine.market_data.get_current_price = AsyncMock(return_value=100.0)
    engine.market_data.get_account_info = AsyncMock(return_value=sample_account)
    engine.market_data.get_positions = AsyncMock(return_value=None)

    engine.risk = MagicMock()
    engine.risk.check_pause = AsyncMock(return_value={"resumed": False, "blocked": False})
    engine.risk.get_circuit_state = AsyncMock(return_value={"stopped": False})
    engine.risk.check = AsyncMock(return_value=RiskResult(passed=True, reason=""))
    engine.risk.record_tick_success = AsyncMock(return_value={"action": "ok", "success_count": 1})
    engine.risk.record_tick_failure = AsyncMock(return_value={"action": "counted", "fail_count": 1})
    engine.risk.reset_circuit_breaker = AsyncMock()
    engine.risk.trip_circuit_breaker = AsyncMock()

    engine.trade = MagicMock()
    engine.trade.execute = AsyncMock(return_value=None)  # 默认不执行实际交易

    engine.strategy_service = MagicMock()
    engine.strategy_service.analyze = AsyncMock(return_value=AggregatedSignal(
        symbol="DOGE/USDT:USDT",
        signal="HOLD", confidence="LOW", reason="mock",
        stop_loss=98.0, take_profit=102.0, source_count=0,
    ))

    engine.coordinator = MagicMock()
    engine.coordinator.analyze = AsyncMock(return_value={
        "signal": "BUY", "confidence": "HIGH", "reason": "mock AI",
        "stop_loss": 97.0, "take_profit": 105.0,
        "source_count": 5, "agent_reports": {}, "position_pct": 100,
    })

    engine.position_manager = MagicMock()
    engine.position_manager.update = AsyncMock(return_value={
        "updated": False, "stop_loss": 98.0, "take_profit": 102.0, "reason": "mock"
    })

    engine.scheduler = MagicMock()
    engine.scheduler._interval = 360

    engine._last_mode = "5_agent"
    engine._last_symbol = "DOGE/USDT:USDT"
    engine._last_leverage = 10
    engine._last_prompt_version = 1

    return engine


# ── Toolkits 测试夹具（200 行，无 open 列）──────────────────────

@pytest.fixture
def sample_ohlcv():
    """200 行模拟 OHLCV 数据，含上升趋势（toolkits 测试用）。"""
    np.random.seed(42)
    n = 200
    close = np.cumsum(np.random.randn(n) * 50) + 95000
    return pd.DataFrame({
        "close": close,
        "high": close + np.random.rand(n) * 200,
        "low": close - np.random.rand(n) * 200,
        "volume": np.random.rand(n) * 1000 + 500,
    }, index=pd.date_range("2026-06-01", periods=n, freq="1min"))


@pytest.fixture
def load_fixtures(sample_ohlcv):
    """将模拟数据注入 toolkits.toolkit_data 缓存。"""
    from app.agents.toolkits.toolkit_data import load_data
    load_data(sample_ohlcv, price=95000.0, equity=10000.0, position={
        "side": "long", "size": 0.1, "entry_price": 94000,
        "unrealized_pnl": 200, "leverage": 1,
    })
