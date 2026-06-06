"""Multi-Agent 协调器 — Supervisor 模式

使用 LangGraph StateGraph 实现 Worker-Manager 模式：
Supervisor LLM 动态调度 Market/Risk/Memory 三个 Worker，
信息充足后交给 Trader 做最终决策。
"""

import asyncio

import pandas as pd

from app.agents.indicator_service import IndicatorService
from app.agents.formats import (
    format_market_text,
    format_memory_text,
    format_position_text,
)
from app.agents.graph import build_supervisor_graph
from app.agents.shared import SupervisorState
from app.agents.schemas import Signal
from app.config import config
from app.logger import get_logger

logger = get_logger()


class AgentCoordinator:
    """Supervisor 模式协调器。

    与旧并行+投票模式不同，这里让 Supervisor LLM 动态决定：
    - 调哪些 Agent（market/risk/memory）
    - 调几次（Supervisor 可循环）
    - 何时提交给 Trader 做最终决策
    """

    def __init__(self):
        self._graph = build_supervisor_graph()

    # ── 主入口 ────────────────────────────────────────────

    async def analyze(
        self,
        df: pd.DataFrame,
        price: float,
        equity: float,
        position: dict | None = None,
    ) -> dict:
        """运行 Supervisor 图，返回与 loop.py 兼容的决策 dict。"""
        # 1. 预计算（统一一次）
        indicators = IndicatorService.latest_indicators(df)
        trend = IndicatorService.trend_analysis(df)
        levels = IndicatorService.support_resistance(df)
        market_state = IndicatorService.market_state(df)

        # 2. 构建文本块
        market_text = format_market_text(price, indicators, trend, levels, market_state)
        position_text = format_position_text(position)
        memory_text = format_memory_text()

        # 3. 构建初始 state
        state: SupervisorState = {
            "messages": [],
            "market_text": market_text,
            "position_text": position_text,
            "memory_text": memory_text,
            "atr_pct": market_state.get("atr_pct", 2.0),
            "market_report": "",
            "risk_report": "",
            "memory_report": "",
            "next_agent": "",
            "final_decision": {},
            "price": price,
            "equity": equity,
        }

        # 4. 运行图（同步 invoke，用 run_in_executor 避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._graph.invoke, state)

        # 5. 提取决策
        decision = result.get("final_decision", {}) if isinstance(result, dict) else {}

        if not decision:
            decision = {
                "signal": "HOLD", "confidence": "LOW",
                "reason": "Supervisor 图未产出决策",
                "stop_loss": price * 0.98, "take_profit": price * 1.02,
                "position_pct": 0,
            }

        # 构建 agent_reports（兼容 loop.py 的持久化格式）
        agent_reports = {}
        if result.get("market_report"):
            agent_reports["market"] = str(result["market_report"])[:200]
        if result.get("risk_report"):
            agent_reports["risk"] = str(result["risk_report"])[:200]
        if result.get("memory_report"):
            agent_reports["memory"] = str(result["memory_report"])[:200]

        return {
            "signal": decision.get("signal", "HOLD"),
            "confidence": decision.get("confidence", "MEDIUM"),
            "reason": decision.get("reason", ""),
            "stop_loss": float(decision.get("stop_loss", price * 0.98)),
            "take_profit": float(decision.get("take_profit", price * 1.02)),
            "position_pct": float(decision.get("position_pct", 0)),
            "source_count": len(agent_reports),
            "agent_reports": agent_reports,
        }
