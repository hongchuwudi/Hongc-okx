"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: test_agent3_timing.py 3-Agent链路耗时测试
描述: 端到端计时 — 3 Agent 快速流水线各阶段耗时

包含:
- 类: TestAgent3Timing — 真实 OKX 行情 + 3 Agent 流水线 + 分段计时
"""

import asyncio
import time
import pytest


@pytest.mark.live
class TestAgent3Timing:

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

    def test_3agent_pipeline_timing(self):
        """完整 3 Agent 流水线耗时测试（含分段计时）"""

        async def run():
            from app.agents.coordinators.coordinator_3 import AgentCoordinator3
            from app.agents.toolkits import toolkit_data
            from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback
            from app.agents.toolkits.communication.toolkit_router import (
                detect_handoff, handle_asks, last_content,
            )
            from app.agents.agent_factory import build_agents_3
            from app.agents.agent_logger import ToolCallLogger, set_current_agent
            from app.agents.agent_status import agent_input, agent_output
            from langchain_core.messages import HumanMessage

            MAX_REDO = 2

            # ── 获取行情 ──
            t0 = time.perf_counter()
            df, price, equity, position = await self._get_market()
            t_market = time.perf_counter() - t0

            print(f"\n{'='*60}")
            print(f"  3 Agent 快速模式耗时测试")
            print(f"{'='*60}")
            print(f"  行情获取: {t_market:.2f}s")
            print(f"  价格: ${price:.4f}  权益: ${equity:.2f}  持仓: {position}")
            print(f"{'='*60}")

            # ── 构建 Agent ──
            t_build = time.perf_counter()
            agents = build_agents_3()
            logger = ToolCallLogger()
            cfg = {"callbacks": [logger]}
            t_build = time.perf_counter() - t_build

            # ── 预加载数据 ──
            toolkit_data.load_data(df, price, equity, position)
            feedback = generate_feedback()

            # ── 基础上下文 ──
            def _empty():
                return {"focus": "", "priority": "",
                        "signal": "", "confidence": "", "report": "", "key_evidence": [],
                        "lesson": "", "recent_win_rate": "", "warning": "", "suggestion": "",
                        "max_position_pct": 10.0, "sl_boundary_pct": 2.0, "tp_boundary_pct": 4.0,
                        "go_no_go": "NO_GO", "risk_assessment": "", "final_decision": {}}

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
            # Phase 1: 超级分析师
            # ══════════════════════════════════════════════════════
            t1 = time.perf_counter()
            set_current_agent("super_analyst")
            await agent_input("super_analyst", f"价格:${price:.0f} 权益:${equity:.0f}")
            sa = await asyncio.to_thread(
                agents["super_analyst"].invoke, {**base, **_empty()}, cfg
            )
            sa, d = await handle_asks(sa, "super_analyst", agents, {**base, **_empty()}, d)
            await agent_output("super_analyst", last_content(sa)[:150], detect_handoff(sa))
            detect_handoff(sa)
            t_super = time.perf_counter() - t1
            print(f"  [超级分析师] {t_super:.1f}s")

            # ══════════════════════════════════════════════════════
            # Phase 2: 风控师
            # ══════════════════════════════════════════════════════
            t2 = time.perf_counter()
            risk_input = {**sa, "messages": list(sa.get("messages", [])),
                          "analysis_signal": sa.get("signal", ""),
                          "analysis_report": last_content(sa)}

            set_current_agent("risk")
            await agent_input("risk", "收到综合报告，开始风险评估")
            risk_result = await asyncio.to_thread(agents["risk"].invoke, risk_input, cfg)
            risk_result, d = await handle_asks(risk_result, "risk", agents, risk_input, d)
            handoff = detect_handoff(risk_result)
            await agent_output("risk", last_content(risk_result)[:150], handoff)

            # 退回重做循环（风控 → 超级分析师）
            redo = 0
            while handoff == "super_analyst" and redo < MAX_REDO:
                redo += 1
                print(f"  [风控→超级分析] 退回重做 (第{redo}次)")
                redo_msgs = list(risk_result.get("messages", []))
                redo_state = {**risk_input, "messages": redo_msgs}
                redo_state["messages"].insert(
                    0, HumanMessage(content=f"风控质疑：{last_content(risk_result)}。请重新评估。")
                )
                set_current_agent("super_analyst")
                sa = await asyncio.to_thread(agents["super_analyst"].invoke, redo_state, cfg)
                sa, d = await handle_asks(sa, "super_analyst", agents, redo_state, d)
                risk_input2 = {
                    **risk_input,
                    "messages": redo_msgs + list(sa.get("messages", [])),
                    "analysis_report": last_content(sa),
                }
                risk_result = await asyncio.to_thread(agents["risk"].invoke, risk_input2, cfg)
                risk_result, d = await handle_asks(risk_result, "risk", agents, risk_input2, d)
                handoff = detect_handoff(risk_result)
            t_risk = time.perf_counter() - t2
            print(f"  [风控师] {t_risk:.1f}s (退回{redo}次)")

            # ══════════════════════════════════════════════════════
            # Phase 3: 交易裁决员
            # ══════════════════════════════════════════════════════
            t3 = time.perf_counter()
            all_msgs = list(sa.get("messages", [])) + list(risk_result.get("messages", []))
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
            t_trader = time.perf_counter() - t3
            print(f"  [交易裁决员] {t_trader:.1f}s")

            # ══════════════════════════════════════════════════════
            # 汇总
            # ══════════════════════════════════════════════════════
            decision = trader_result.get("final_decision", {})
            total_agent = t_super + t_risk + t_trader
            total_all = t_market + t_build + total_agent

            print(f"\n{'='*60}")
            print(f"  耗时汇总 (3 Agent)")
            print(f"{'='*60}")
            print(f"  行情获取:        {t_market:>6.1f}s")
            print(f"  Agent 构建:      {t_build:>6.1f}s")
            print(f"  ─────────────────────────")
            print(f"  超级分析师:      {t_super:>6.1f}s")
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
