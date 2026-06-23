"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_strategy.py 策略分析
描述: 每个 tick 的策略分析 — AI 多 Agent 或技术指标，含 AI 失败降级逻辑

降级链路（优先级从高到低）:
1. 余额不足降级 — DeepSeek 余额 < 0.05 CNY 时，本 tick 直接走技术指标，
   不调用 agent（避免无谓的 402 失败）。仅本 tick 跳过，不改 use_multi_agent。
2. AI 调用失败降级 — agent 抛异常时，降级为技术指标 + 连续失败计数。

包含:
- 函数: tick_analyze_strategy — 执行策略分析，返回 Signal + 原始决策字典
- 函数: _analyze_technical — 技术指标分析（降级与 tech 模式共用）
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
        # 余额检查：DeepSeek 余额不足时本 tick 降级为技术指标，不走 agent
        from app.services.agent.agent_balance_service import check_balance_sufficient
        sufficient, balance = await check_balance_sufficient()
        if not sufficient:
            logger.warning(
                f"AI 余额不足({balance} CNY < 阈值)，本 tick 降级为技术指标方案"
            )
            signal = await _analyze_technical(engine, df, position,
                                              reason=f"AI余额不足({balance} CNY)，降级技术指标")
            return signal, decision

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
            signal = await _analyze_technical(engine, df, position,
                                              reason=f"AI降级(连续{engine._agent_fail_count}次): {str(ai_err)[:100]}")
            logger.info(f"[降级] 技术指标: {signal.signal} (信心: {signal.confidence})")
            if engine._agent_fail_count >= 5:
                logger.critical(f"AI 连续失败 {engine._agent_fail_count} 次，建议检查 API 配置或切换 agent_mode=tech")
    else:
        signal = await _analyze_technical(engine, df, position, reason="")
        logger.info(f"信号: {signal.signal} (信心: {signal.confidence})")

    return signal, decision


# 技术指标分析 — tech 模式与降级路径共用。
# reason 非空时表示降级来源，写入 agent_reports 供前端展示。
async def _analyze_technical(engine, df: pd.DataFrame, position: dict | None,
                              reason: str = "") -> Signal:
    """技术指标策略分析，返回清洗后的 Signal。"""
    signal = await engine.strategy_service.analyze(df, position, engine._symbol)
    signal.signal = _clean_signal(signal.signal)
    signal.reason = _clean_signal(signal.reason)
    if reason:
        signal.agent_reports = {"degraded": reason}
    else:
        signal.agent_reports = {}
    signal.source_count = 0
    return signal
