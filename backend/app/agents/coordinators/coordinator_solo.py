"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: coordinator_solo.py 单Agent协调器
描述: 1 Agent 急速模式 — 预计算指标注入 + Solo Agent 决策

包含:
- 类: AgentCoordinatorSolo — 单 Agent 编排（预计算→注入→决策）
- 函数: analyze — 指标预计算 → 上下文注入 → Solo调用 → 解析决策
"""

import asyncio

import pandas as pd
from langchain_core.messages import HumanMessage

from app.agents.agent_factory import build_agent_solo
from app.agents.models import get_solo_llm
from app.agents.toolkits.toolkit_data import load_data, _position
from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback
from app.agents.toolkits.tools.toolkit_calc_risk import evaluate_position_risk, calc_max_position, calc_sl_tp
from app.agents.toolkits.communication.toolkit_router import last_content
from app.agents.agent_logger import ToolCallLogger, set_current_agent
from app.agents.agent_status import agent_input, agent_output
from app.agents.indicator_service import IndicatorService
from app.services.config.runtime import get_runtime
from app.core.logger import get_logger

logger = get_logger()


# 1 Agent 急速模式 — 预计算所有指标，Agent 直接看数据做决策。
class AgentCoordinatorSolo:

    def __init__(self):
        self._agent = build_agent_solo()
        self._llm = get_solo_llm()
        self._logger = ToolCallLogger()
        self._cfg = {"callbacks": [self._logger]}
        logger.info("1 Agent Solo 急速模式就绪 (预计算注入)")

    # ── 辅助 ──────────────────────────────────────────────

    def _base(self, price: float, equity: float, df: pd.DataFrame) -> dict:
        pos = _position()
        pos_text = (f"持仓: {'多头' if pos['side']=='long' else '空头'} {pos.get('size',0)}张 "
                    f"入场${pos.get('entry_price',0):.2f} 浮亏${pos.get('unrealized_pnl',0):+.2f} "
                    f"杠杆{pos.get('leverage',1)}x") if pos and pos.get('side') else "无持仓"

        # ── 预计算技术指标 ──
        latest = IndicatorService.latest_indicators(df)
        atr = IndicatorService.atr_pct(df)
        rsi = IndicatorService.calc_rsi(df)
        trend = IndicatorService.trend_analysis(df)

        # MACD 金叉/死叉判断
        macd_v = latest["macd"]
        macd_s = latest["macd_signal"]
        macd_cross = "金叉(看涨)" if macd_v > macd_s else "死叉(看跌)" if macd_v < macd_s else "持平"

        # 量比判断
        vr = latest["volume_ratio"]
        vol_desc = "放量" if vr > 1.5 else "缩量" if vr < 0.5 else "正常"

        # ── 预计算风控参数 ──
        pos_risk = evaluate_position_risk()
        max_pos_med = calc_max_position("MEDIUM", atr)
        max_pos_high = calc_max_position("HIGH", atr)
        sl_tp_long = calc_sl_tp("long", atr)
        sl_tp_short = calc_sl_tp("short", atr)

        # ── 运行时配置 ──
        rt_leverage = int(get_runtime("leverage"))
        rt_order_amount = float(get_runtime("order_amount"))
        rt_max_position = float(get_runtime("max_position_ratio"))

        context = (
            f"=== 预计算数据（已算好，无需调指标/风控工具） ===\n"
            f"价格: ${price:.4f}  权益: ${equity:.2f}\n"
            f"杠杆: {rt_leverage}x  单笔金额: ${rt_order_amount:.0f}  最大仓位: {rt_max_position*100:.0f}%\n"
            f"{pos_text}\n"
            f"\n--- 技术指标 ---\n"
            f"RSI(14): {rsi:.1f} ({'超买>70' if rsi>70 else '超卖<30' if rsi<30 else '中性'})\n"
            f"MACD: {macd_v:.5f} / 信号:{macd_s:.5f} → {macd_cross}\n"
            f"SMA20: ${latest['sma_20']:.4f}  价格{'上方' if price > latest['sma_20'] else '下方'}\n"
            f"SMA50: ${latest['sma_50']:.4f}  价格{'上方' if price > latest['sma_50'] else '下方'}\n"
            f"布林带: 上轨${latest['bb_upper']:.4f} 下轨${latest['bb_lower']:.4f} 位置{latest['bb_position']:.0%}\n"
            f"ATR: {atr:.2f}%  量比: {vr:.1f} ({vol_desc})\n"
            f"趋势: 短期{trend['short_term']} 中期{trend['medium_term']} MACD{trend['macd']} → {trend['overall']}\n"
            f"\n--- 风控预计算 ---\n"
            f"{pos_risk}\n"
            f"中等信心仓位: {max_pos_med}\n"
            f"高信心仓位: {max_pos_high}\n"
            f"做多SL/TP: {sl_tp_long}\n"
            f"做空SL/TP: {sl_tp_short}\n"
            f"=========================================\n"
            f"所有指标已预先计算好。只需调历史工具(get_trade_stats/recent_trades/lessons)回顾历史，然后直接做决策！"
        )
        return {"messages": [HumanMessage(content=context)],
                "remaining_steps": 6, "price": price, "equity": equity}

    def _empty(self) -> dict:
        return {"signal": "", "confidence": "", "reason": "",
                "position_pct": 0, "stop_loss": 0, "take_profit": 0,
                "risk_rating": "", "final_decision": {}}

    # ── 主入口 ────────────────────────────────────────────

    async def analyze(
        self, df: pd.DataFrame, price: float, equity: float, position: dict | None = None,
    ) -> dict:
        self._logger._loop = asyncio.get_running_loop()
        load_data(df, price, equity, position)

        # 反馈注入
        feedback = generate_feedback()
        base = self._base(price, equity, df)
        base["messages"].insert(0, HumanMessage(content=feedback))
        logger.info(f"[反馈] {feedback.split(chr(10))[0]}")

        # 单次 LLM 调用（只看历史 → 直接决策）
        set_current_agent("solo")
        await agent_input("solo", f"价格:${price:.4f} 权益:${equity:.0f}")
        result = await asyncio.to_thread(self._agent.invoke, {**base, **self._empty()}, self._cfg)
        raw_output = last_content(result)
        await agent_output("solo", raw_output[:2000])
        logger.info("[Solo Agent] 完成")

        # 从最后一条消息中解析决策（三层兜底 + 一次模型重试）
        from app.agents.parser import parse_agent_output, build_retry_prompt
        parsed = parse_agent_output(raw_output)
        if not parsed.success:
            retry_msg = HumanMessage(content=build_retry_prompt(raw_output[:2000], parsed.error))
            retry_resp = await asyncio.to_thread(self._llm.invoke, [retry_msg])
            retry_text = retry_resp.content if hasattr(retry_resp, 'content') else str(retry_resp)
            parsed = parse_agent_output(retry_text)
            logger.info(f"Solo 重试解析: success={parsed.success} strategy={parsed.strategy}")
        decision = parsed.data if parsed.success else {}
        if not decision.get("signal"):
            logger.warning(f"Solo Agent 解析失败(含重试): {parsed.error[:100]}")
            decision = {"signal": "HOLD", "confidence": "LOW", "reason": "未产出决策",
                        "stop_loss": price * 0.98, "take_profit": price * 1.02, "position_pct": 0}

        return {
            "signal": decision.get("signal", "HOLD"),
            "confidence": decision.get("confidence", "MEDIUM"),
            "reason": decision.get("reason", ""),
            "stop_loss": float(decision.get("stop_loss", price * 0.98)),
            "take_profit": float(decision.get("take_profit", price * 1.02)),
            "position_pct": float(decision.get("position_pct", 0)),
            "source_count": 1,
            "agent_reports": {
                "solo": last_content(result),
            },
        }
