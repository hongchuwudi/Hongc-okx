"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: test_agent_timing.py 多Agent链路耗时测试
描述: 端到端计时 — 5 Agent 完整流水线各阶段耗时

包含:
- 类: TestAgentTiming — 真实 OKX 行情 + 5 Agent 流水线 + 分段计时
"""

import asyncio
import time
import pytest


@pytest.mark.live
class TestAgentTiming:

    async def _get_market(self):
        from app.exchange.client import ExchangeClient
        exchange = ExchangeClient()

        df = await exchange.fetch_ohlcv("DOGE/USDT:USDT", "1m", 200)
        ticker = await exchange.fetch_ticker("DOGE/USDT:USDT")
        price = ticker.get("last", 0) or ticker.get("close", 0)
        balance = await exchange.fetch_balance()
        positions = await exchange.fetch_positions(["DOGE/USDT:USDT"])

        equity = float(balance.get("USDT", {}).get("total", 10000) or 10000)
        pos = None
        for p in positions:
            if float(p.get("contracts", 0)) > 0:
                pos = {
                    "side": p["side"],
                    "size": float(p["contracts"]),
                    "entry_price": float(p.get("entryPrice", 0)),
                    "unrealized_pnl": float(p.get("unrealizedPnl", 0)),
                    "leverage": int(p.get("leverage", 1)),
                }
                break

        return df, price, equity, pos

    def test_full_pipeline_timing(self):
        """完整 5 Agent 流水线耗时测试（含分段计时）"""

        async def run():
            from app.agents.coordinators.coordinator_5 import AgentCoordinator
            from app.agents.toolkits import toolkit_data
            from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback
            from app.agents.toolkits.communication.toolkit_router import (
                detect_handoff, handle_asks, last_content,
            )
            from app.agents.agent_factory import build_agents
            from app.agents.agent_logger import ToolCallLogger, set_current_agent
            from app.agents.agent_status import agent_input, agent_output
            from langchain_core.messages import HumanMessage

            MAX_REDO = 2

            # ── 获取行情 ──
            t0 = time.perf_counter()
            df, price, equity, position = await self._get_market()
            t_market = time.perf_counter() - t0

            print(f"\n{'='*60}")
            print(f"  多 Agent 链路耗时测试")
            print(f"{'='*60}")
            print(f"  行情获取: {t_market:.2f}s")
            print(f"  价格: ${price:.4f}  权益: ${equity:.2f}  持仓: {position}")
            print(f"{'='*60}")

            # ── 构建 Agent ──
            t_build = time.perf_counter()
            agents = build_agents()
            logger = ToolCallLogger()
            cfg = {"callbacks": [logger]}
            t_build = time.perf_counter() - t_build

            # ── 预加载数据 ──
            toolkit_data.load_data(df, price, equity, position)
            feedback = generate_feedback()

            # ── 基础上下文 ──
            def _empty():
                return {
                    "scheduler_focus": "", "scheduler_priority": "", "scheduler_questions": "",
                    "analysis_signal": "", "analysis_confidence": "", "analysis_report": "",
                    "analysis_key_evidence": "",
                    "reviewer_lesson": "", "reviewer_warning": "", "reviewer_suggestion": "",
                    "max_position_pct": 10.0, "sl_boundary_pct": 2.0, "tp_boundary_pct": 4.0,
                    "go_no_go": "NO_GO", "risk_assessment": "", "final_decision": {},
                }

            pos_text = "无持仓"
            if position and position.get("side"):
                pos_text = (
                    f"持仓: {'多头' if position['side']=='long' else '空头'} "
                    f"{position.get('size',0)}张 "
                    f"入场${position.get('entry_price',0):.2f} "
                    f"浮亏${position.get('unrealized_pnl',0):+.2f} "
                    f"杠杆{position.get('leverage',1)}x"
                )

            base = {
                "messages": [
                    HumanMessage(content=feedback),
                    HumanMessage(content=(
                        f"=== 市场数据(已预加载，无需调工具获取) ===\n"
                        f"BTC价格: ${price:,.2f}\n"
                        f"账户权益: ${equity:,.2f}\n"
                        f"{pos_text}\n"
                        f"================================\n"
                        f"请直接分析决策，不要调用get_price/get_position等查询工具。"
                    )),
                ],
                "remaining_steps": 10, "price": price, "equity": equity,
            }
            d = 0

            # ══════════════════════════════════════════════════════
            # Phase 1: 调度师
            # ══════════════════════════════════════════════════════
            t1 = time.perf_counter()
            set_current_agent("scheduler")
            await agent_input("scheduler", f"价格:${price:.0f} 权益:${equity:.0f}")
            sch = await asyncio.to_thread(
                agents["scheduler"].invoke, {**base, **_empty()}, cfg
            )
            sch, d = await handle_asks(sch, "scheduler", agents, {**base, **_empty()}, d)
            await agent_output("scheduler", last_content(sch)[:150], detect_handoff(sch))
            detect_handoff(sch)
            t_scheduler = time.perf_counter() - t1
            print(f"  [调度师] {t_scheduler:.1f}s")

            # ══════════════════════════════════════════════════════
            # Phase 2: 分析师 + 复盘师 并行
            # ══════════════════════════════════════════════════════
            t2 = time.perf_counter()
            shared = {**sch, "messages": list(sch.get("messages", []))}
            set_current_agent("analyst")
            await agent_input("analyst", "收到调度师指令，开始技术分析")
            set_current_agent("reviewer")
            await agent_input("reviewer", "收到调度师指令，开始历史复盘")
            analyst, reviewer = await asyncio.gather(
                asyncio.to_thread(agents["analyst"].invoke, shared, cfg),
                asyncio.to_thread(agents["reviewer"].invoke, shared, cfg),
            )
            analyst, d = await handle_asks(analyst, "analyst", agents, shared, d)
            await agent_output("analyst", last_content(analyst)[:150], detect_handoff(analyst))
            detect_handoff(analyst)
            reviewer, d = await handle_asks(reviewer, "reviewer", agents, shared, d)
            await agent_output("reviewer", last_content(reviewer)[:150], detect_handoff(reviewer))
            detect_handoff(reviewer)
            t_parallel = time.perf_counter() - t2
            print(f"  [分析师 ∥ 复盘师] {t_parallel:.1f}s (并行)")

            # ══════════════════════════════════════════════════════
            # Phase 3: 风控师
            # ══════════════════════════════════════════════════════
            t3 = time.perf_counter()
            risk_msgs = list(analyst.get("messages", [])) + list(reviewer.get("messages", []))
            risk_input = {
                **sch, "messages": risk_msgs,
                "analysis_signal": analyst.get("analysis_signal", ""),
                "analysis_report": last_content(analyst),
                "reviewer_lesson": last_content(reviewer),
            }
            set_current_agent("risk")
            await agent_input("risk", "收到分析报告，开始风险评估")
            risk_result = await asyncio.to_thread(agents["risk"].invoke, risk_input, cfg)
            risk_result, d = await handle_asks(risk_result, "risk", agents, risk_input, d)
            handoff = detect_handoff(risk_result)
            await agent_output("risk", last_content(risk_result)[:150], handoff)

            # 退回重做循环
            redo = 0
            while handoff == "analyst" and redo < MAX_REDO:
                redo += 1
                print(f"  [风控→分析] 退回重做 (第{redo}次)")
                redo_msgs = list(risk_result.get("messages", []))
                redo_state = {**risk_input, "messages": redo_msgs}
                redo_state["messages"].insert(
                    0, HumanMessage(content=f"风控质疑：{last_content(risk_result)}。请重新评估。")
                )
                set_current_agent("analyst")
                analyst = await asyncio.to_thread(agents["analyst"].invoke, redo_state, cfg)
                analyst, d = await handle_asks(analyst, "analyst", agents, redo_state, d)
                risk_input2 = {
                    **risk_input,
                    "messages": redo_msgs + list(analyst.get("messages", [])),
                    "analysis_report": last_content(analyst),
                }
                risk_result = await asyncio.to_thread(agents["risk"].invoke, risk_input2, cfg)
                risk_result, d = await handle_asks(risk_result, "risk", agents, risk_input2, d)
                handoff = detect_handoff(risk_result)
            t_risk = time.perf_counter() - t3
            print(f"  [风控师] {t_risk:.1f}s (退回{redo}次)")

            # ══════════════════════════════════════════════════════
            # Phase 4: 交易裁决员
            # ══════════════════════════════════════════════════════
            t4 = time.perf_counter()
            all_msgs = risk_msgs + list(risk_result.get("messages", []))
            trader_state = {
                **risk_input, "messages": all_msgs,
                "max_position_pct": risk_result.get("max_position_pct", 10.0),
                "go_no_go": risk_result.get("go_no_go", "NO_GO"),
                "risk_assessment": last_content(risk_result),
            }
            set_current_agent("trader")
            await agent_input("trader", "收到风控边界，开始综合裁决")
            trader_result = await asyncio.to_thread(agents["trader"].invoke, trader_state, cfg)
            trader_result, _ = await handle_asks(trader_result, "trader", agents, trader_state, d)
            await agent_output("trader", last_content(trader_result)[:150])
            t_trader = time.perf_counter() - t4
            print(f"  [交易裁决员] {t_trader:.1f}s")

            # ══════════════════════════════════════════════════════
            # 汇总
            # ══════════════════════════════════════════════════════
            decision = trader_result.get("final_decision", {})
            total_agent = t_scheduler + t_parallel + t_risk + t_trader
            total_all = t_market + t_build + total_agent

            print(f"\n{'='*60}")
            print(f"  耗时汇总")
            print(f"{'='*60}")
            print(f"  行情获取:        {t_market:>6.1f}s")
            print(f"  Agent 构建:      {t_build:>6.1f}s")
            print(f"  ─────────────────────────")
            print(f"  调度师:          {t_scheduler:>6.1f}s")
            print(f"  分析师∥复盘师:   {t_parallel:>6.1f}s (并行)")
            print(f"  风控师:          {t_risk:>6.1f}s")
            print(f"  交易裁决员:      {t_trader:>6.1f}s")
            print(f"  ─────────────────────────")
            print(f"  Agent 合计:      {total_agent:>6.1f}s")
            print(f"  全部总计:        {total_all:>6.1f}s")
            print(f"{'='*60}")
            print(f"\n  最终信号: {decision.get('signal', 'HOLD')}")
            print(f"  置信度:   {decision.get('confidence', 'MEDIUM')}")
            print(f"  理由:     {decision.get('reason', '')[:200]}")

            # 断言
            assert decision.get("signal", "HOLD") in ("BUY", "SELL", "HOLD")

        asyncio.run(run())
