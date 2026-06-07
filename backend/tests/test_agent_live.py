"""
端到端测试: 真实 OKX 模拟盘行情 + 5 Agent 完整流水线

需要: OKX 通过代理连通
运行: pytest tests/test_agent_live.py -v -s
"""

import asyncio
import pytest


@pytest.mark.live
class TestAgentLive:
    """真实环境端到端测试。"""

    async def _get_market(self):
        from app.exchange.client import ExchangeClient
        exchange = ExchangeClient()

        # 直接调底层 ccxt，不走 MarketDataService
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

    def test_full_pipeline(self):
        """5 Agent 真实管道 — OKX 实盘行情 + DeepSeek LLM。"""

        async def run():
            from app.agents.coordinator import AgentCoordinator

            df, price, equity, position = await self._get_market()
            print(f"行情: ${price:.2f}  权益: ${equity:.2f}  持仓: {position}")

            coordinator = AgentCoordinator()
            decision = await coordinator.analyze(df, price, equity, position)

            print(f"\n======== 最终决策 ========")
            print(f"信号:     {decision['signal']}")
            print(f"置信度:   {decision['confidence']}")
            print(f"仓位:     {decision['position_pct']}%")
            print(f"止损:     ${decision['stop_loss']:.2f}")
            print(f"止盈:     ${decision['take_profit']:.2f}")
            print(f"理由:     {decision['reason'][:200]}")
            print(f"参与Agent: {decision['source_count']}")

            assert decision["signal"] in ("BUY", "SELL", "HOLD")
            assert decision["stop_loss"] > 0
            assert decision["take_profit"] > 0

        asyncio.run(run())
