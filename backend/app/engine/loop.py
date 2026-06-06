"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: loop.py 中文名
描述: 交易引擎主循环 — 整合所有服务，驱动一轮完整的交易周期

包含:
- 类: TradingEngine — 交易引擎，事件驱动的主循环，协调各服务完成交易
"""

import json
import traceback
from datetime import datetime

from app.config import config
from app.database import SyncSession, get_redis, get_sync_session
from app.exchange.client import ExchangeClient
from app.entities.system import SystemStatus
from app.entities.trading import EquitySnapshot, Trade
from app.services.market_data import MarketDataService
from app.services.risk import RiskService
from app.services.scheduler import SchedulerService
from app.services.strategy import StrategyService
from app.services.trade import TradeService
from app.strategies.technical import TechnicalStrategy
from app.agents.indicator_service import IndicatorService
from app.memory import memory_store
from app.logger import get_logger

logger = get_logger()


class TradingEngine:
    """交易引擎 — 事件驱动的主循环，协调市场数据、策略分析、风控、交易执行"""

    def __init__(self):
        # 基础设施
        self.exchange = ExchangeClient()                      # 交易所客户端

        # 服务层
        self.market_data = MarketDataService(self.exchange)   # 市场数据服务
        self.risk = RiskService()                             # 风控服务
        self.trade = TradeService(self.exchange, vars(config.trade))  # 交易执行服务
        self.scheduler = SchedulerService(
            interval_seconds=config.trade.tick_interval_seconds  # 调度间隔
        )

        # Multi-Agent 协作模式（AI 可用时启用）
        has_ai = config.ai.provider == "deepseek" and config.ai.deepseek_api_key
        if has_ai:
            from app.agents.coordinator import AgentCoordinator
            self.coordinator = AgentCoordinator()
            self.use_multi_agent = True
            logger.info("启用 Multi-Agent 协作模式（3 Agent 并行+投票）")
        else:
            # 无 AI 时使用纯技术指标策略
            self.strategy_service = StrategyService(strategies=[TechnicalStrategy()])
            self.use_multi_agent = False
            logger.warning("AI 客户端未配置，使用技术指标策略")

        # 动态持仓管理（每 tick 更新追踪止损）
        from app.agents.position_manager import PositionManager
        self.position_manager = PositionManager(self.exchange)

        # 记忆追踪 ID（用于平仓时正确关联开仓记忆记录）
        self._open_trade_memory_id: int | None = None

        # 交易对符号
        self._symbol = config.trade.symbol

    async def run(self) -> None:
        """启动引擎，开始调度循环"""
        logger.info("=" * 50)
        logger.info("交易引擎启动")
        logger.info(f"交易对: {self._symbol}")
        if self.use_multi_agent:
            logger.info("模式: Multi-Agent (4 Agent 团队)")
        else:
            logger.info(f"策略: {self.strategy_service.strategy_names}")
        logger.info("=" * 50)

        # 启动定时调度循环
        await self.scheduler.run_loop(self._tick)

    async def _tick(self) -> None:
        """单个交易周期：获取数据 -> 策略分析 -> 动态持仓 -> 风控 -> 执行 -> 持久化"""
        tick_start = datetime.now()
        logger.info(f"--- Tick {tick_start.strftime('%H:%M:%S')} ---")

        # 连续失败计数（用于熔断）
        if not hasattr(self, '_fail_count'):
            self._fail_count = 0  # type: ignore

        try:
            # 1. 获取市场数据和账户信息
            df = await self.market_data.get_ohlcv(self._symbol, config.trade.timeframe, config.trade.data_points)
            price = await self.market_data.get_current_price(self._symbol)
            account = await self.market_data.get_account_info()
            position = await self.market_data.get_positions(self._symbol)

            # 2. 策略分析 — Multi-Agent 或传统策略模式
            if self.use_multi_agent:
                decision = await self.coordinator.analyze(
                    df, price, account["equity"], position
                )
                signal = type('Signal', (), {})()
                signal.signal = decision.get("signal", "HOLD")
                signal.confidence = decision.get("confidence", "MEDIUM")
                signal.reason = decision.get("reason", "")
                signal.stop_loss = float(decision.get("stop_loss", price * 0.98))
                signal.take_profit = float(decision.get("take_profit", price * 1.02))
                signal.source_count = decision.get("source_count", 0)
                signal.agent_reports = decision.get("agent_reports", {})
                logger.info(f"Multi-Agent: {signal.signal} (信心: {signal.confidence}) 来源: {signal.source_count}个")
            else:
                signal = await self.strategy_service.analyze(df, position)
                signal.agent_reports = {}
                logger.info(f"信号: {signal.signal} (信心: {signal.confidence})")

            # 3. 动态持仓管理 — 每 tick 更新追踪止损（包括 HOLD 时也执行）
            if position and position.get("side") and position.get("size", 0) > 0:
                atr_pct = IndicatorService.atr_pct(df)
                pm_result = await self.position_manager.update(
                    position=position,
                    current_price=price,
                    atr_pct=atr_pct,
                    current_sl=signal.stop_loss,
                    current_tp=signal.take_profit,
                )
                if pm_result.get("updated"):
                    signal.stop_loss = pm_result["stop_loss"]
                    signal.take_profit = pm_result["take_profit"]

            # 4. 记录 AI 决策到记忆（每次 tick 都存）
            last_close = float(df["close"].iloc[-1]) if len(df) > 0 else price
            market_summary = ""
            try:
                sma20 = float(df["close"].rolling(20).mean().iloc[-1])
                trend = "上涨" if last_close > sma20 else "下跌"
                rsi_val = IndicatorService.calc_rsi(df)
                market_summary = f"{trend}趋势 RSI={rsi_val:.0f}"
            except Exception:
                pass
            memory_id = memory_store.add(
                signal=signal.signal, confidence=signal.confidence,
                reason=signal.reason, price=last_close,
                market_state=market_summary,
            )
            if signal.signal != "HOLD":
                self._open_trade_memory_id = memory_id

            # 5. 风控检查
            risk_result = await self.risk.check(
                signal=signal.signal,
                equity=account["equity"],
                current_position_value=abs(position["size"] * position.get("entry_price", price))
                if position else 0,
            )
            if not risk_result.passed:
                logger.warning(f"风控拦截: {risk_result.reason}")
                if "熔断" in risk_result.reason:
                    await self._publish_event({"type": "circuit_breaker", "reason": risk_result.reason})
                await self._persist(price, account, position, signal, None)
                return

            # 6. 执行交易
            trade_result = None
            if signal.signal != "HOLD":
                trade_result = await self.trade.execute(
                    signal=signal.signal,
                    price=price,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    amount_usdt=config.trade.base_usdt_amount,
                )
                if trade_result:
                    logger.info(f"交易执行: {trade_result.get('action')}")
                    action = trade_result.get("action", "")
                    # 平仓时更新记忆中的交易结果
                    if action in ("close", "reverse"):
                        if self._open_trade_memory_id is not None:
                            memory_store.update_outcome(
                                self._open_trade_memory_id, trade_result.get("pnl", 0)
                            )
                            self._open_trade_memory_id = None

            # 7. 持久化（PostgreSQL + Redis 缓存）
            await self._persist(price, account, position, signal, trade_result)

            # 8. 发布事件（Redis Pub/Sub → 推送到 WebSocket 前端）
            await self._publish_event({
                "type": "tick_complete",
                "timestamp": tick_start.isoformat(),
                "btc_price": price,
                "equity": account["equity"],
                "signal": signal.signal,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "position": position,
            })

            logger.info(f"Tick 完成，耗时: {(datetime.now() - tick_start).total_seconds():.1f}s")

        except Exception as e:
            self._fail_count += 1
            logger.error(f"Tick 异常 (连续失败 {self._fail_count} 次): {e}")
            traceback.print_exc()
            # 连续失败 10 次自动熔断
            if self._fail_count >= 10:
                logger.critical("连续 10 次 Tick 失败，触发熔断！请检查系统状态。")
                await self.risk.trip_circuit_breaker(f"连续 {self._fail_count} 次 tick 失败")
        else:
            # 成功执行则重置失败计数
            self._fail_count = 0

    async def _persist(
        self,
        price: float,
        account: dict,
        position: dict | None,
        signal,
        trade_result: dict | None,
    ) -> None:
        """写入 PostgreSQL（在线程池中执行避免阻塞事件循环）+ Redis 缓存"""
        import asyncio

        def _write_db():
            """在线程池中执行数据库写入操作"""
            sess: SyncSession = get_sync_session()
            try:
                # 系统状态 upsert（单行表）
                row = sess.query(SystemStatus).filter_by(id=1).first()
                if row is None:
                    row = SystemStatus(id=1)
                    sess.add(row)
                row.status = "running"
                row.last_update = datetime.now()
                row.balance = account["balance"]
                row.equity = account["equity"]
                row.btc_price = price
                row.ai_signal = signal.signal
                row.ai_confidence = signal.confidence
                row.ai_reason = signal.reason
                # 保存 Agent 报告（Multi-Agent 模式）
                if hasattr(signal, 'agent_reports') and signal.agent_reports:
                    import json as _json
                    # 清理 LLM 输出中的破损 Unicode (lone surrogates)
                    def _clean(s):
                        return s.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')
                    cleaned = {k: _clean(v) for k, v in signal.agent_reports.items()}
                    row.ai_reason = _json.dumps(
                        {"reason": _clean(signal.reason), "agents": cleaned},
                        ensure_ascii=False
                    )
                row.ai_stop_loss = float(signal.stop_loss)
                row.ai_take_profit = float(signal.take_profit)
                row.ai_timestamp = datetime.now()
                row.timeframe = config.trade.timeframe
                if position:
                    row.position_side = position["side"]
                    row.position_size = position["size"]
                    row.position_entry_price = position["entry_price"]
                    row.position_unrealized_pnl = position["unrealized_pnl"]
                else:
                    row.position_side = None
                    row.position_size = 0
                    row.position_entry_price = 0
                    row.position_unrealized_pnl = 0
                sess.commit()

                # 记录权益快照
                snap = EquitySnapshot(timestamp=datetime.now(), equity=account["equity"])
                sess.add(snap)
                sess.commit()

                # 记录交易
                if trade_result:
                    trade = Trade(
                        timestamp=datetime.now(), signal=signal.signal,
                        price=price, amount=trade_result.get("amount", 0),
                        confidence=signal.confidence, reason=signal.reason, pnl=0,
                    )
                    sess.add(trade)
                    sess.commit()
            except Exception as e:
                logger.error(f"数据持久化失败: {e}")
                sess.rollback()
            finally:
                sess.close()

        await asyncio.get_event_loop().run_in_executor(None, _write_db)

        # 更新 Redis 缓存
        try:
            redis = await get_redis()
            # 最新信号缓存
            await redis.hset("signal:btc:latest", mapping={
                "signal": signal.signal, "confidence": signal.confidence,
                "reason": signal.reason, "stop_loss": str(signal.stop_loss),
                "take_profit": str(signal.take_profit),
                "timestamp": datetime.now().isoformat(),
            })
            await redis.expire("signal:btc:latest", 300)
            # 信号历史列表（保留最近 50 条）
            await redis.lpush("signal:btc:history", json.dumps({
                "signal": signal.signal, "confidence": signal.confidence,
                "timestamp": datetime.now().isoformat(),
            }))
            await redis.ltrim("signal:btc:history", 0, 49)
        except Exception as e:
            logger.error(f"Redis 缓存更新失败: {e}")

    async def _publish_event(self, data: dict) -> None:
        """发布事件到 Redis Pub/Sub 频道，供 WebSocket 推送到前端"""
        try:
            redis = await get_redis()
            await redis.publish("ws:channel:updates", json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"事件推送失败: {e}")
