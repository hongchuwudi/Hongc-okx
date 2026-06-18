"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_tick_persist.py 持久化与异常处理测试
描述: 验证 tick_persist 的持久化推送 + 异常处理（暂停/停止两档）

包含:
- TestPersistAndNotify — persist + cache + publish + circuit_clear + agent_logs
- TestHandleError — 失败记录（警告/暂停/停止三档）
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.engine.result.signal import Signal


class TestPersistAndNotify:
    """tick 完成后的持久化 + 推送 + 熔断解除。"""

    @pytest.mark.asyncio
    async def test_calls_persist_and_cache(self, mock_engine, sample_account):
        """验证 persist_tick 和 cache_signal 被调用。"""
        sig = Signal(signal="BUY", confidence="HIGH", reason="测试", stop_loss=95.0, take_profit=105.0)
        mock_engine.risk.record_tick_success = AsyncMock(return_value={})
        tick_start = datetime.now()

        with patch("app.engine.loop.tick_persist.persist_tick", AsyncMock()) as mock_persist, \
             patch("app.engine.loop.tick_persist.cache_signal", AsyncMock()) as mock_cache, \
             patch("app.engine.loop.tick_persist.publish_event", AsyncMock()) as mock_pub, \
             patch("app.agents.status.save_tick_agent_logs", AsyncMock()) as mock_logs:
            from app.engine.loop.tick_persist import tick_persist_and_notify
            await tick_persist_and_notify(
                mock_engine, tick_start, 100.0, sample_account, None, sig, None,
            )

        mock_persist.assert_called_once()
        mock_cache.assert_called_once_with(sig)
        mock_pub.assert_called_once()
        mock_logs.assert_called_once()
        mock_engine.risk.record_tick_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_tick_complete_event(self, mock_engine, sample_account):
        """验证 WebSocket 推送事件包含正确的 tick_complete 数据结构。"""
        sig = Signal(signal="SELL", confidence="LOW", reason="回调", stop_loss=102.0, take_profit=96.0)
        mock_engine.risk.record_tick_success = AsyncMock(return_value={})
        tick_start = datetime(2026, 6, 23, 10, 30, 0)

        with patch("app.engine.loop.tick_persist.persist_tick", AsyncMock()), \
             patch("app.engine.loop.tick_persist.cache_signal", AsyncMock()), \
             patch("app.engine.loop.tick_persist.publish_event", AsyncMock()) as mock_pub, \
             patch("app.agents.status.save_tick_agent_logs", AsyncMock()):
            from app.engine.loop.tick_persist import tick_persist_and_notify
            await tick_persist_and_notify(
                mock_engine, tick_start, 99.5, sample_account, None, sig, {"action": "open"},
            )

        event = mock_pub.call_args.args[0]
        assert event["type"] == "tick_complete"
        assert event["btc_price"] == 99.5
        assert event["equity"] == 10000.0
        assert event["signal"] == "SELL"
        assert event["confidence"] == "LOW"
        assert event["reason"] == "回调"

    @pytest.mark.asyncio
    async def test_circuit_cleared_logs(self, mock_engine, sample_account):
        """熔断自动解除时记录日志。"""
        sig = Signal(signal="BUY", confidence="MEDIUM")
        mock_engine.risk.record_tick_success = AsyncMock(return_value={
            "action": "cleared", "success_count": 5,
        })

        with patch("app.engine.loop.tick_persist.persist_tick", AsyncMock()), \
             patch("app.engine.loop.tick_persist.cache_signal", AsyncMock()), \
             patch("app.engine.loop.tick_persist.publish_event", AsyncMock()), \
             patch("app.agents.status.save_tick_agent_logs", AsyncMock()):
            from app.engine.loop.tick_persist import tick_persist_and_notify
            await tick_persist_and_notify(
                mock_engine, datetime.now(), 100.0, sample_account, None, sig, None,
            )

        # 无异常即通过


class TestHandleError:
    """Tick 异常处理：失败记录 + 熔断暂停/停止。"""

    @pytest.mark.asyncio
    async def test_records_failure(self, mock_engine):
        """异常时调用 record_tick_failure。"""
        mock_engine.risk.record_tick_failure = AsyncMock(return_value={})
        error = ValueError("测试异常")

        with patch("app.engine.loop.tick_persist.publish_event", AsyncMock()):
            from app.engine.loop.tick_persist import tick_handle_error
            await tick_handle_error(mock_engine, error)

        mock_engine.risk.record_tick_failure.assert_called_once_with("ValueError")

    @pytest.mark.asyncio
    async def test_paused_triggers_warning(self, mock_engine):
        """连续失败达暂停阈值时记录警告。"""
        mock_engine.risk.record_tick_failure = AsyncMock(return_value={
            "action": "paused", "fail_count": 3, "pause_minutes": 5,
        })

        with patch("app.engine.loop.tick_persist.publish_event", AsyncMock()):
            from app.engine.loop.tick_persist import tick_handle_error
            await tick_handle_error(mock_engine, RuntimeError("超时"))

        # 暂停时不调用 trip_circuit_breaker
        mock_engine.risk.trip_circuit_breaker.assert_not_called()

    @pytest.mark.asyncio
    async def test_stopped_trips_circuit_and_publishes(self, mock_engine):
        """连续失败达停止阈值时熔断停引擎 + 推送事件。"""
        mock_engine.risk.record_tick_failure = AsyncMock(return_value={
            "action": "stopped", "fail_count": 10,
        })

        with patch("app.engine.loop.tick_persist.publish_event", AsyncMock()) as mock_pub:
            from app.engine.loop.tick_persist import tick_handle_error
            await tick_handle_error(mock_engine, ConnectionError("网络断开"))

        mock_engine.risk.trip_circuit_breaker.assert_called_once()
        event = mock_pub.call_args.args[0]
        assert event["type"] == "circuit_breaker"
        assert event["state"] == "stopped"
        assert "10" in event["reason"]
