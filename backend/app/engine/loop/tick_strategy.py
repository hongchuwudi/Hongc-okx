"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_strategy.py 策略分析
描述: 每个 tick 的策略分析 — AI 多 Agent 或技术指标，含 AI 失败降级逻辑

包含:
- 函数: tick_analyze_strategy — 执行策略分析，返回 Signal + 原始决策字典
"""

import pandas as pd

from app.engine.result.signal import Signal
from app.engine.loop.tick_emoji import _clean_signal
from app.core.logger import get_logger

logger = get_logger()


async def tick_analyze_strategy(engine, df: pd.DataFrame, price: float,
                                 account: dict, position: dict | None
                                 ) -> tuple[Signal, dict | None]:
    """策略分析：AI 多 Agent 或技术指标。

    返回: (signal, decision) — decision 仅在 multi_agent 模式非 None。
    """
    decision = None

    if engine.use_multi_agent:
        try:
            decision = await engine.coordinator.analyze(df, price, account["equity"], position)
            signal = Signal(
                signal=_clean_signal(decision.get("signal", "HOLD")),
                confidence=_clean_signal(decision.get("confidence", "MEDIUM")),
                reason=_clean_signal(decision.get("reason", "")),
                stop_loss=float(decision.get("stop_loss", price * 0.98)),
                take_profit=float(decision.get("take_profit", price * 1.02)),
                source_count=decision.get("source_count", 0),
                agent_reports=decision.get("agent_reports", {}),
            )
            engine._agent_fail_count = 0
            logger.info(f"Multi-Agent: {signal.signal} (信心: {signal.confidence}) 来源: {signal.source_count}个")
        except Exception as ai_err:
            engine._agent_fail_count += 1
            logger.warning(f"AI 调用失败 (连续{engine._agent_fail_count}次)，降级为技术指标: {type(ai_err).__name__}: {ai_err}")
            signal = await engine.strategy_service.analyze(df, position, engine._symbol)
            signal.signal = _clean_signal(signal.signal)
            signal.reason = _clean_signal(signal.reason)
            signal.agent_reports = {"degraded": f"AI降级(连续{engine._agent_fail_count}次): {str(ai_err)[:100]}"}
            signal.source_count = 0
            logger.info(f"[降级] 技术指标: {signal.signal} (信心: {signal.confidence})")
            if engine._agent_fail_count >= 5:
                logger.critical(f"AI 连续失败 {engine._agent_fail_count} 次，建议检查 API 配置或切换 agent_mode=tech")
    else:
        signal = await engine.strategy_service.analyze(df, position, engine._symbol)
        signal.signal = _clean_signal(signal.signal)
        signal.reason = _clean_signal(signal.reason)
        signal.agent_reports = {}
        logger.info(f"信号: {signal.signal} (信心: {signal.confidence})")

    return signal, decision
