"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_persist.py 持久化与推送
描述: 每个 tick 的持久化（PG/Redis）+ WebSocket 推送 + 熔断解除 + Agent 日志

包含:
- 函数: tick_persist_and_notify — 持久化 + 推送
- 函数: tick_handle_error — 异常处理（记录失败 / 熔断暂停 / 熔断停止）
"""

from datetime import datetime

from app.engine.result.signal import Signal
from app.services.persistence import persist_tick, cache_signal, publish_event
from app.core.logger import get_logger

logger = get_logger()


async def tick_persist_and_notify(engine, tick_start: datetime, price: float,
                                   account: dict, position: dict | None,
                                   signal: Signal, trade_result: dict | None) -> None:
    """持久化 tick 数据 + WebSocket 推送 + 熔断状态更新 + Agent 日志。"""
    # 持久化
    await persist_tick(price, account, position, signal, trade_result)
    await cache_signal(signal)

    # WebSocket 推送
    await publish_event({
        "type": "tick_complete",
        "timestamp": tick_start.isoformat(),
        "btc_price": price,
        "equity": account["equity"],
        "signal": signal.signal,
        "confidence": signal.confidence,
        "reason": signal.reason,
        "position": position,
    })

    logger.info(f"Tick 完成，耗时: {(datetime.now() - tick_start).total_seconds():.1f}s")

    # 熔断自动解除检查
    cb_result = await engine.risk.record_tick_success()
    if cb_result.get("action") == "cleared":
        logger.info(f"连续 {cb_result['success_count']} 次成功，熔断已自动解除")

    # Agent 决策日志入库
    from app.agents.status import save_tick_agent_logs
    await save_tick_agent_logs(
        engine.agent_mode_display,
        signal=signal.signal, confidence=signal.confidence,
        reason=signal.reason, stop_loss=signal.stop_loss,
        take_profit=signal.take_profit, source_count=signal.source_count,
    )


async def tick_handle_error(engine, error: Exception) -> None:
    """Tick 异常处理：记录失败 / 熔断暂停 / 熔断停引擎。"""
    err_name = type(error).__name__
    logger.error(f"Tick 异常: {err_name}: {error}")

    cb_result = await engine.risk.record_tick_failure(err_name)
    if cb_result.get("action") == "paused":
        logger.warning(f"连续 {cb_result['fail_count']} 次失败，暂停 {cb_result['pause_minutes']} 分钟")
    elif cb_result.get("action") == "stopped":
        logger.critical(f"连续 {cb_result['fail_count']} 次失败，熔断停引擎！请人工检查后手动重启")
        await engine.risk.trip_circuit_breaker(
            f"连续 {cb_result['fail_count']} 次 tick 失败 ({err_name})，引擎已停止"
        )
        await publish_event({
            "type": "circuit_breaker",
            "state": "stopped",
            "reason": f"连续 {cb_result['fail_count']} 次失败，引擎已停止",
        })
