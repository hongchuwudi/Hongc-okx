"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: test_agent_solo_timing.py 单Agent链路耗时测试
描述: 端到端计时 — 1 Agent 急速流水线耗时

包含:
- 类: TestAgentSoloTiming — 真实 OKX 行情 + Solo Agent 计时
"""

import asyncio
import time
import pytest


@pytest.mark.live
class TestAgentSoloTiming:

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

    def test_solo_pipeline_timing(self):
        """Solo Agent 急速流水线耗时测试"""

        async def run():
            from app.agents.agent_factory import build_agent_solo
            from app.agents.toolkits import toolkit_data
            from app.agents.toolkits.tools.toolkit_calc_feedback import generate_feedback
            from app.agents.toolkits.tools.toolkit_calc_risk import evaluate_position_risk, calc_max_position, calc_sl_tp
            from app.agents.toolkits.communication.toolkit_router import last_content
            from app.agents.agent_logger import ToolCallLogger, set_current_agent
            from app.agents.agent_status import agent_input, agent_output
            from app.agents.indicator_service import IndicatorService
            from langchain_core.messages import HumanMessage

            # ── 获取行情 ──
            t0 = time.perf_counter()
            df, price, equity, position = await self._get_market()
            t_market = time.perf_counter() - t0

            print(f"\n{'='*60}")
            print(f"  Solo Agent 急速模式耗时测试 (预计算注入)")
            print(f"{'='*60}")
            print(f"  行情获取: {t_market:.2f}s")
            print(f"  价格: ${price:.4f}  权益: ${equity:.2f}  持仓: {position}")
            print(f"{'='*60}")

            # ── 构建 Agent ──
            t_build = time.perf_counter()
            agent = build_agent_solo()
            logger = ToolCallLogger()
            cfg = {"callbacks": [logger]}
            t_build = time.perf_counter() - t_build

            # ── 预加载数据 ──
            toolkit_data.load_data(df, price, equity, position)
            feedback = generate_feedback()

            # ── 预计算指标（同 coordinator_solo._base）──
            latest = IndicatorService.latest_indicators(df)
            atr = IndicatorService.atr_pct(df)
            rsi = IndicatorService.calc_rsi(df)
            trend = IndicatorService.trend_analysis(df)
            macd_v = latest["macd"]; macd_s = latest["macd_signal"]
            macd_cross = "金叉(看涨)" if macd_v > macd_s else "死叉(看跌)" if macd_v < macd_s else "持平"
            vr = latest["volume_ratio"]
            vol_desc = "放量" if vr > 1.5 else "缩量" if vr < 0.5 else "正常"
            pos_risk = evaluate_position_risk()
            max_pos_med = calc_max_position("MEDIUM", atr)
            sl_tp_long = calc_sl_tp("long", atr)
            sl_tp_short = calc_sl_tp("short", atr)

            # ── 基础上下文 ──
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
                        f"=== 预计算数据（已算好，无需调指标/风控工具） ===\n"
                        f"价格: ${price:.4f}  权益: ${equity:.2f}\n"
                        f"{pos_text}\n"
                        f"\n--- 技术指标 ---\n"
                        f"RSI(14): {rsi:.1f} ({'超买>70' if rsi>70 else '超卖<30' if rsi<30 else '中性'})\n"
                        f"MACD: {macd_v:.5f} / 信号:{macd_s:.5f} → {macd_cross}\n"
                        f"SMA20: ${latest['sma_20']:.4f}  SMA50: ${latest['sma_50']:.4f}\n"
                        f"布林带: 上轨${latest['bb_upper']:.4f} 下轨${latest['bb_lower']:.4f} 位置{latest['bb_position']:.0%}\n"
                        f"ATR: {atr:.2f}%  量比: {vr:.1f} ({vol_desc})\n"
                        f"趋势: 短期{trend['short_term']} 中期{trend['medium_term']} → {trend['overall']}\n"
                        f"\n--- 风控预计算 ---\n"
                        f"{pos_risk}\n"
                        f"中等信心仓位: {max_pos_med}\n"
                        f"做多SL/TP: {sl_tp_long}\n"
                        f"做空SL/TP: {sl_tp_short}\n"
                        f"=========================================\n"
                        f"只需调历史工具(get_trade_stats/recent_trades/lessons)回顾历史，然后直接做决策！"
                    )),
                ],
                "remaining_steps": 6, "price": price, "equity": equity,
            }
            empty = {"signal": "", "confidence": "", "reason": "",
                     "position_pct": 0, "stop_loss": 0, "take_profit": 0,
                     "risk_rating": "", "final_decision": {}}

            # ══════════════════════════════════════════════════════
            # Solo Agent 单次调用
            # ══════════════════════════════════════════════════════
            t1 = time.perf_counter()
            set_current_agent("solo")
            await agent_input("solo", f"价格:${price:.0f} 权益:${equity:.0f}")
            result = await asyncio.to_thread(agent.invoke, {**base, **empty}, cfg)
            await agent_output("solo", last_content(result)[:150])
            t_solo = time.perf_counter() - t1
            print(f"  [Solo Agent] {t_solo:.1f}s")

            # ══════════════════════════════════════════════════════
            # 汇总
            # ══════════════════════════════════════════════════════
            decision = result.get("final_decision", {})
            total_all = t_market + t_build + t_solo

            print(f"\n{'='*60}")
            print(f"  耗时汇总 (1 Agent)")
            print(f"{'='*60}")
            print(f"  行情获取:        {t_market:>6.1f}s")
            print(f"  Agent 构建:      {t_build:>6.1f}s")
            print(f"  ─────────────────────────")
            print(f"  Solo Agent:      {t_solo:>6.1f}s")
            print(f"  ─────────────────────────")
            print(f"  全部总计:        {total_all:>6.1f}s")
            print(f"{'='*60}")
            print(f"\n  最终信号: {decision.get('signal', 'HOLD')}")
            print(f"  置信度:   {decision.get('confidence', 'MEDIUM')}")
            print(f"  理由:     {decision.get('reason', '')[:200]}")

            assert decision.get("signal", "HOLD") in ("BUY", "SELL", "HOLD")

        asyncio.run(run())
