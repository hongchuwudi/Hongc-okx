"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: coordinator_3.py 3-Agent协调器
描述: 3 Agent Swarm 快速模式 — Super-Analyst → Risk → Trader

包含:
- 类: AgentCoordinator3 — 3 Agent Swarm 编排（快速流水线）
- 函数: analyze — 超级分析→风控(可退回)→裁决
"""

import asyncio

import pandas as pd
from langchain_core.messages import HumanMessage

from app.agents.agent_factory import build_agents_3
from app.agents.toolkits.toolkit_data import load_data
from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback
from app.agents.toolkits.communication.toolkit_router import detect_handoff, handle_asks, last_content
from app.agents.agent_logger import ToolCallLogger, set_current_agent
from app.agents.status import agent_input, agent_output
from app.services.config.runtime import get_runtime
from app.core.logger import get_logger

logger = get_logger()
MAX_REDO = 2


# 3 Agent Swarm — Super-Analyst → Risk → Trader，精简流水线。
class AgentCoordinator3:

    def __init__(self):
        self._agents = build_agents_3()
        self._super_analyst = self._agents["super_analyst"]
        self._risk = self._agents["risk"]
        self._trader = self._agents["trader"]
        self._logger = ToolCallLogger()
        self._cfg = {"callbacks": [self._logger]}
        logger.info("3 Agent Swarm 就绪 (快速模式)")

    # ── 辅助 ──────────────────────────────────────────────

    def _base(self, price: float, equity: float) -> dict:
        from app.agents.toolkits.toolkit_data import _position, _df
        pos = _position()
        pos_text = (f"持仓: {'多头' if pos['side']=='long' else '空头'} {pos.get('size',0)}张 "
                    f"入场${pos.get('entry_price',0) or 0:.2f} 浮亏${pos.get('unrealized_pnl',0):+.2f} "
                    f"杠杆{pos.get('leverage',1)}x") if pos and pos.get('side') and pos.get('entry_price') not in (None, 0) else ("无持仓" if not pos or not pos.get('side') else f"持仓: {'多头' if pos['side']=='long' else '空头'} {pos.get('size',0)}张 入场价未知 浮亏${pos.get('unrealized_pnl',0):+.2f} 杠杆{pos.get('leverage',1)}x")

        rt_leverage = int(get_runtime("leverage"))
        rt_order_amount = float(get_runtime("order_amount"))
        rt_max_position = float(get_runtime("max_position_ratio"))

        context = (
            f"=== 市场数据(已预加载，无需调工具获取) ===\n"
            f"价格: ${price:,.2f}  权益: ${equity:,.2f}  杠杆: {rt_leverage}x  单笔: ${rt_order_amount:.0f}\n"
            f"{pos_text}\n"
            f"================================\n"
            f"请直接分析决策，不要调用get_price/get_position等查询工具。"
        )
        return {"messages": [HumanMessage(content=context)],
                "remaining_steps": 10, "price": price, "equity": equity}

    def _empty(self) -> dict:
        return {"focus": "", "priority": "",
                "signal": "", "confidence": "", "report": "", "key_evidence": [],
                "lesson": "", "recent_win_rate": "", "warning": "", "suggestion": "",
                "max_position_pct": 10.0, "sl_boundary_pct": 2.0, "tp_boundary_pct": 4.0,
                "go_no_go": "NO_GO", "risk_assessment": "", "final_decision": {}}

    # ── 主入口 ────────────────────────────────────────────

    async def analyze(
        self, df: pd.DataFrame, price: float, equity: float, position: dict | None = None,
    ) -> dict:
        self._logger._loop = asyncio.get_running_loop()
        load_data(df, price, equity, position)
        # 学习闭环：检查上一轮决策结果
        feedback = generate_feedback()
        base = self._base(price, equity)
        base["messages"].insert(0, HumanMessage(content=feedback))
        logger.info(f"[反馈] {feedback.split(chr(10))[0]}")
        d = 0

        # Phase 1: 超级分析师（合并调度+技术分析+历史复盘）
        set_current_agent("super_analyst")
        await agent_input("super_analyst", f"价格:${price:.0f} 权益:${equity:.0f}")
        sa = await asyncio.to_thread(self._super_analyst.invoke, {**base, **self._empty()}, self._cfg)
        sa, d = await handle_asks(sa, "super_analyst", self._agents, {**base, **self._empty()}, d)
        await agent_output("super_analyst", last_content(sa)[:500], detect_handoff(sa))
        detect_handoff(sa)
        logger.info("[超级分析师] 完成")

        # Phase 2: 风控师
        risk_input = {**sa, "messages": list(sa.get("messages", [])),
                      "analysis_signal": sa.get("signal", ""),
                      "analysis_report": last_content(sa)}

        set_current_agent("risk")
        await agent_input("risk", "收到综合报告，开始风险评估")
        risk_result = await asyncio.to_thread(self._risk.invoke, risk_input, self._cfg)
        risk_result, d = await handle_asks(risk_result, "risk", self._agents, risk_input, d)
        handoff = detect_handoff(risk_result)
        await agent_output("risk", last_content(risk_result)[:500], handoff)
        logger.info("[风控师] 完成")

        # 退回重做循环（风控 → 超级分析师）
        redo = 0
        while handoff == "super_analyst" and redo < MAX_REDO:
            redo += 1
            logger.info(f"[风控→超级分析] 退回重做 (第{redo}次)")
            redo_msgs = list(risk_result.get("messages", []))
            redo_state = {**risk_input, "messages": redo_msgs}
            redo_state["messages"].insert(0, HumanMessage(
                content=f"风控质疑：{last_content(risk_result)}。请重新评估。"))
            set_current_agent("super_analyst")
            sa = await asyncio.to_thread(self._super_analyst.invoke, redo_state, self._cfg)
            sa, d = await handle_asks(sa, "super_analyst", self._agents, redo_state, d)
            risk_input2 = {**risk_input,
                           "messages": redo_msgs + list(sa.get("messages", [])),
                           "analysis_report": last_content(sa)}
            risk_result = await asyncio.to_thread(self._risk.invoke, risk_input2, self._cfg)
            risk_result, d = await handle_asks(risk_result, "risk", self._agents, risk_input2, d)
            handoff = detect_handoff(risk_result)
            logger.info(f"[风控师·重审{redo}] 完成")

        if redo >= MAX_REDO and handoff == "super_analyst":
            logger.warning(f"风控退回达上限({MAX_REDO}次)，强制进入裁决")

        # Phase 3: 交易裁决员
        all_msgs = list(sa.get("messages", [])) + list(risk_result.get("messages", []))
        trader_state = {**risk_input, "messages": all_msgs,
                        "max_position_pct": risk_result.get("max_position_pct", 10.0),
                        "go_no_go": risk_result.get("go_no_go", "NO_GO"),
                        "risk_assessment": last_content(risk_result)}
        set_current_agent("trader")
        await agent_input("trader", "收到风控边界，开始综合裁决")
        trader_result = await asyncio.to_thread(self._trader.invoke, trader_state, self._cfg)
        trader_result, _ = await handle_asks(trader_result, "trader", self._agents, trader_state, d)
        raw_output = last_content(trader_result)
        await agent_output("trader", raw_output[:2000])
        logger.info("[交易裁决员] 完成")

        from app.agents.parser import parse_agent_output, build_retry_prompt
        from app.agents.models import get_trader_llm
        parsed = parse_agent_output(raw_output)
        if not parsed.success:
            retry_msg = HumanMessage(content=build_retry_prompt(raw_output[:2000], parsed.error))
            retry_llm = get_trader_llm()
            retry_resp = await asyncio.to_thread(retry_llm.invoke, [retry_msg])
            retry_text = retry_resp.content if hasattr(retry_resp, 'content') else str(retry_resp)
            parsed = parse_agent_output(retry_text)
            logger.info(f"Trader 重试解析(3Agent): success={parsed.success} strategy={parsed.strategy}")
        decision = parsed.data if parsed.success else {}
        if not decision.get("signal"):
            logger.warning(f"Trader 解析失败(3Agent,含重试): {parsed.error[:100]}")
            decision = {"signal": "HOLD", "confidence": "LOW", "reason": "未产出决策",
                        "stop_loss": price * 0.98, "take_profit": price * 1.02, "position_pct": 0}

        go = risk_result.get("go_no_go", "")
        if go == "NO_GO" and decision.get("signal") != "HOLD":
            decision["signal"] = "HOLD"

        return {
            "signal": decision.get("signal", "HOLD"),
            "confidence": decision.get("confidence", "MEDIUM"),
            "reason": decision.get("reason", ""),
            "stop_loss": float(decision.get("stop_loss", price * 0.98)),
            "take_profit": float(decision.get("take_profit", price * 1.02)),
            "position_pct": float(decision.get("position_pct", 0)),
            "source_count": 3,
            "agent_reports": {
                "super_analyst": last_content(sa),
                "risk": last_content(risk_result),
                "trader": last_content(trader_result),
            },
        }
