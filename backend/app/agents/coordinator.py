"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: coordinator.py Agent协调器
描述: 5 Agent Swarm 主流程 — asyncio 并行 + 移交/对话/退回/记忆

包含:
- 类: AgentCoordinator — 5 Agent Swarm 编排（薄薄一层流水线）
- 函数: analyze — 调度→分析+复盘∥→风控(可退回)→裁决
"""

import asyncio

import pandas as pd
from langchain_core.messages import HumanMessage

from app.agents.agent_factory import build_agents
from app.agents.toolkits.toolkit_data import load_data
from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback
from app.agents.toolkits.communication.toolkit_router import detect_handoff, handle_asks, last_content
from app.agents.toolkits.toolkit_logger import ToolCallLogger, set_current_agent
from app.agents.toolkits.toolkit_agent_status import agent_input, agent_output
from app.logger import get_logger

logger = get_logger()
MAX_REDO = 2


class AgentCoordinator:
    """5 Agent Swarm — 移交/对话/退回/记忆。构建逻辑在 agent_factory，路由在 swarm/toolkit_router。"""

    def __init__(self):
        self._agents = build_agents()
        self._scheduler = self._agents["scheduler"]
        self._analyst = self._agents["analyst"]
        self._reviewer = self._agents["reviewer"]
        self._risk = self._agents["risk"]
        self._trader = self._agents["trader"]
        self._logger = ToolCallLogger()
        self._cfg = {"callbacks": [self._logger]}  # 注入到每次 invoke 的 config
        logger.info("5 Agent Swarm 就绪")

    # ── 辅助 ──────────────────────────────────────────────

    def _base(self, price: float, equity: float) -> dict:
        return {"messages": [HumanMessage(content=f"价格:${price:.0f} 权益:${equity:.0f}")],
                "remaining_steps": 10, "price": price, "equity": equity}

    def _empty(self) -> dict:
        return {"scheduler_focus": "", "scheduler_priority": "", "scheduler_questions": "",
                "analysis_signal": "", "analysis_confidence": "", "analysis_report": "", "analysis_key_evidence": "",
                "reviewer_lesson": "", "reviewer_warning": "", "reviewer_suggestion": "",
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

        # Phase 1: 调度师
        set_current_agent("scheduler")
        await agent_input("scheduler", f"价格:${price:.0f} 权益:${equity:.0f}")
        sch = await asyncio.to_thread(self._scheduler.invoke, {**base, **self._empty()}, self._cfg)
        sch, d = await handle_asks(sch, "scheduler", self._agents, {**base, **self._empty()}, d)
        await agent_output("scheduler", last_content(sch)[:150], detect_handoff(sch))
        detect_handoff(sch)
        logger.info("[调度师] 完成")

        # Phase 2: 分析师 + 复盘师 并行
        shared = {**sch, "messages": list(sch.get("messages", []))}
        set_current_agent("analyst")
        await agent_input("analyst", "收到调度师指令，开始技术分析")
        set_current_agent("reviewer")
        await agent_input("reviewer", "收到调度师指令，开始历史复盘")
        analyst, reviewer = await asyncio.gather(
            asyncio.to_thread(self._analyst.invoke, shared, self._cfg),
            asyncio.to_thread(self._reviewer.invoke, shared, self._cfg),
        )
        analyst, d = await handle_asks(analyst, "analyst", self._agents, shared, d)
        await agent_output("analyst", last_content(analyst)[:150], detect_handoff(analyst))
        detect_handoff(analyst)
        logger.info("[分析师] 完成")
        reviewer, d = await handle_asks(reviewer, "reviewer", self._agents, shared, d)
        await agent_output("reviewer", last_content(reviewer)[:150], detect_handoff(reviewer))
        detect_handoff(reviewer)
        logger.info("[复盘师] 完成")

        # Phase 3: 风控师
        risk_msgs = list(analyst.get("messages", [])) + list(reviewer.get("messages", []))
        risk_input = {**sch, "messages": risk_msgs,
                      "analysis_signal": analyst.get("analysis_signal", ""),
                      "analysis_report": last_content(analyst),
                      "reviewer_lesson": last_content(reviewer)}

        set_current_agent("risk")
        await agent_input("risk", f"收到分析报告，开始风险评估")
        risk_result = await asyncio.to_thread(self._risk.invoke, risk_input, self._cfg)
        risk_result, d = await handle_asks(risk_result, "risk", self._agents, risk_input, d)
        handoff = detect_handoff(risk_result)
        await agent_output("risk", last_content(risk_result)[:150], handoff)
        logger.info("[风控师] 完成")

        # 退回重做循环
        redo = 0
        while handoff == "analyst" and redo < MAX_REDO:
            redo += 1
            logger.info(f"[风控→分析] 退回重做 (第{redo}次)")
            redo_msgs = list(risk_result.get("messages", []))
            redo_state = {**risk_input, "messages": redo_msgs}
            redo_state["messages"].insert(0, HumanMessage(content=f"风控质疑：{last_content(risk_result)}。请重新评估。"))
            set_current_agent("analyst")
            analyst = await asyncio.to_thread(self._analyst.invoke, redo_state, self._cfg)
            analyst, d = await handle_asks(analyst, "analyst", self._agents, redo_state, d)
            risk_input2 = {**risk_input, "messages": redo_msgs + list(analyst.get("messages", [])),
                           "analysis_report": last_content(analyst)}
            risk_result = await asyncio.to_thread(self._risk.invoke, risk_input2, self._cfg)
            risk_result, d = await handle_asks(risk_result, "risk", self._agents, risk_input2, d)
            handoff = detect_handoff(risk_result)
            logger.info(f"[风控师·重审{redo}] 完成")

        if redo >= MAX_REDO and handoff == "analyst":
            logger.warning(f"风控退回达上限({MAX_REDO}次)，强制进入裁决")

        # Phase 4: 交易裁决员
        all_msgs = risk_msgs + list(risk_result.get("messages", []))
        trader_state = {**risk_input, "messages": all_msgs,
                        "max_position_pct": risk_result.get("max_position_pct", 10.0),
                        "go_no_go": risk_result.get("go_no_go", "NO_GO"),
                        "risk_assessment": last_content(risk_result)}
        set_current_agent("trader")
        await agent_input("trader", f"收到风控边界，开始综合裁决")
        trader_result = await asyncio.to_thread(self._trader.invoke, trader_state, self._cfg)
        trader_result, _ = await handle_asks(trader_result, "trader", self._agents, trader_state, d)
        await agent_output("trader", last_content(trader_result)[:150])
        logger.info("[交易裁决员] 完成")

        decision = trader_result.get("final_decision", {})
        if not decision:
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
            "source_count": 5, "agent_reports": {},
        }
