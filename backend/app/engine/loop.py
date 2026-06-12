"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: loop.py 交易引擎主循环
描述: 交易引擎主循环 — 整合所有服务，驱动一轮完整的交易周期，所有配置即时生效

包含:
- 类: TradingEngine — 交易引擎，事件驱动的主循环，协调各服务完成交易
"""

from datetime import datetime

from app.config import config
from app.exchange.client import ExchangeClient
from app.engine.signal import Signal
from app.engine.runtime import RuntimeSyncMixin
from app.services.market.market_data import MarketDataService
from app.services.risk.risk import RiskService
from app.services.engine.scheduler import SchedulerService
from app.services.trading.strategy import StrategyService
from app.services.trading.trade import TradeService
from app.engine.persistence import persist_tick, cache_signal, publish_event
from app.services.agent.agent_coordinator_service import (
    create_position_manager, get_indicator_service,
)
from app.services.config.runtime import get_runtime_async
from app.strategies.technical import TechnicalStrategy
from app.services.memory.memory import memory_service
from app.core.logger import get_logger

IndicatorService = get_indicator_service()
logger = get_logger()


# 交易引擎 — 事件驱动的主循环，协调行情、策略、风控、交易、持久化全流程
class TradingEngine(RuntimeSyncMixin):

    def __init__(self):
        self.exchange = ExchangeClient()
        self.market_data = MarketDataService(self.exchange)
        self.risk = RiskService()
        self.trade = TradeService(self.exchange, vars(config.trade))
        self.scheduler = SchedulerService(interval_seconds=360)

        self.strategy_service = StrategyService(strategies=[TechnicalStrategy()])

        self.coordinator = None
        self.use_multi_agent = False
        self.agent_mode_display = "未初始化"
        self._agent_fail_count = 0

        self._last_mode: str = ""
        self._last_symbol: str = ""
        self._last_leverage: int = 0
        self._last_prompt_version: int = 0

        self.position_manager = create_position_manager(self.exchange, config.trade.symbol)
        self._open_trade_memory_id: int | None = None
        self._symbol = config.trade.symbol

        self._probe_count = 0

    # ── 启动引擎 ──────────────────────────────────────

    async def run(self) -> None:
        await self._sync_runtime()
        logger.info("=" * 50)
        logger.info("交易引擎启动")
        logger.info(f"交易对: {self._symbol}")
        logger.info(f"模式: {self.agent_mode_display}")
        logger.info("=" * 50)

        try:
            await self.exchange.set_position_mode(hedged=False)
            logger.info("持仓模式: 单向")
        except Exception as e:
            from app.exchange.base import parse_okx_error
            logger.warning(f"持仓模式设置跳过: {parse_okx_error(e)}")

        try:
            await self.exchange.set_leverage(self._symbol, int(await get_runtime_async("leverage")))
            logger.info(f"杠杆: {await get_runtime_async('leverage')}x")
        except Exception as e:
            from app.exchange.base import parse_okx_error
            logger.warning(f"杠杆设置跳过: {parse_okx_error(e)}")

        await self.risk.reset_circuit_breaker()
        logger.info("已重置熔断状态")

        await self.scheduler.run_loop(self._tick)

    # ── 单个交易周期 ──────────────────────────────────

    async def _tick(self) -> None:
        tick_start = datetime.now()
        logger.info(f"--- Tick {tick_start.strftime('%H:%M:%S')} ---")

        # 0. 智能熔断：暂停冷却检查 / 已停止则直接跳过
        pause_info = await self.risk.check_pause()
        if pause_info.get("resumed"):
            logger.info("熔断冷却期满，自动恢复交易")
        if pause_info.get("blocked"):
            remaining = pause_info.get("remaining_s", 0)
            logger.warning(f"熔断暂停中，剩余 {remaining}s，跳过本轮 tick")
            await publish_event({
                "type": "circuit_breaker",
                "state": "paused",
                "reason": f"熔断暂停中，剩余 {remaining}s",
            })
            return

        cb_state = await self.risk.get_circuit_state()
        if cb_state["stopped"]:
            logger.warning("熔断已停止引擎，跳过本轮 tick (请通过 API 或前端重置)")
            return

        try:
            # 1. 同步运行时配置（所有字段即时生效）
            await self._sync_runtime()

            # 2. 获取市场数据
            timeframe = await get_runtime_async("timeframe")
            data_points = int(await get_runtime_async("data_points"))

            if self.exchange.use_backup:
                self._probe_count += 1
                if self._probe_count >= 10:
                    self._probe_count = 0
                    self.exchange.switch_to_primary()

            for attempt in range(2):
                try:
                    df = await self.market_data.get_ohlcv(self._symbol, timeframe, data_points)
                    price = await self.market_data.get_current_price(self._symbol)
                    account = await self.market_data.get_account_info()
                    position = await self.market_data.get_positions(self._symbol)
                    break
                except Exception as net_err:
                    if attempt == 0 and self.exchange.switch_to_backup():
                        logger.warning(f"行情获取失败，切换代理重试: {net_err}")
                        continue
                    raise

            # 3. 策略分析
            if self.use_multi_agent:
                try:
                    decision = await self.coordinator.analyze(df, price, account["equity"], position)
                    signal = Signal(
                        signal=decision.get("signal", "HOLD"),
                        confidence=decision.get("confidence", "MEDIUM"),
                        reason=decision.get("reason", ""),
                        stop_loss=float(decision.get("stop_loss", price * 0.98)),
                        take_profit=float(decision.get("take_profit", price * 1.02)),
                        source_count=decision.get("source_count", 0),
                        agent_reports=decision.get("agent_reports", {}),
                    )
                    self._agent_fail_count = 0
                    logger.info(f"Multi-Agent: {signal.signal} (信心: {signal.confidence}) 来源: {signal.source_count}个")
                except Exception as ai_err:
                    self._agent_fail_count += 1
                    logger.warning(f"AI 调用失败 (连续{self._agent_fail_count}次)，降级为技术指标: {type(ai_err).__name__}: {ai_err}")
                    signal = await self.strategy_service.analyze(df, position, self._symbol)
                    signal.agent_reports = {"degraded": f"AI降级(连续{self._agent_fail_count}次): {str(ai_err)[:100]}"}
                    signal.source_count = 0
                    logger.info(f"[降级] 技术指标: {signal.signal} (信心: {signal.confidence})")
                    if self._agent_fail_count >= 5:
                        logger.critical(f"AI 连续失败 {self._agent_fail_count} 次，建议检查 API 配置或切换 agent_mode=tech")
            else:
                signal = await self.strategy_service.analyze(df, position, self._symbol)
                signal.agent_reports = {}
                logger.info(f"信号: {signal.signal} (信心: {signal.confidence})")

            # 4. 动态持仓管理（移动止盈止损）
            if position and position.get("side") and position.get("size", 0) > 0:
                atr_pct = IndicatorService.atr_pct(df)
                pm_result = await self.position_manager.update(
                    position=position, current_price=price, atr_pct=atr_pct,
                    current_sl=signal.stop_loss, current_tp=signal.take_profit,
                )
                if pm_result.get("updated"):
                    signal.stop_loss = pm_result["stop_loss"]
                    signal.take_profit = pm_result["take_profit"]

            # 5. AI 决策记忆（用于长期学习优化）
            last_close = float(df["close"].iloc[-1]) if len(df) > 0 else price
            market_summary = ""
            try:
                sma20 = float(df["close"].rolling(20).mean().iloc[-1])
                trend = "上涨" if last_close > sma20 else "下跌"
                rsi_val = IndicatorService.calc_rsi(df)
                market_summary = f"{trend}趋势 RSI={rsi_val:.0f}"
            except Exception:
                pass
            memory_id = memory_service.add(
                signal=signal.signal, confidence=signal.confidence,
                reason=signal.reason, price=last_close, market_state=market_summary,
            )
            if signal.signal != "HOLD":
                self._open_trade_memory_id = memory_id

            # 6. 风控检查（熔断、回撤限制、日亏损上限）
            risk_result = await self.risk.check(
                signal=signal.signal, equity=account["equity"],
                current_position_value=abs(position["size"] * position.get("entry_price", price)) if position else 0,
            )
            if not risk_result.passed:
                logger.warning(f"风控拦截: {risk_result.reason}")
                if "熔断" in risk_result.reason:
                    await publish_event({"type": "circuit_breaker", "reason": risk_result.reason})
                await persist_tick(price, account, position, signal, None)
                return

            # 7. 执行交易
            trade_result = None
            if signal.signal != "HOLD":
                order_amount = float(await get_runtime_async("order_amount"))
                leverage = int(await get_runtime_async("leverage"))
                if self.use_multi_agent:
                    position_pct = float(decision.get("position_pct", 100))
                    order_amount = order_amount * (position_pct / 100)
                trade_result = await self.trade.execute(
                    signal=signal.signal, price=price,
                    stop_loss=signal.stop_loss, take_profit=signal.take_profit,
                    amount_usdt=order_amount, leverage=leverage,
                )
                if trade_result:
                    logger.info(f"交易执行: {trade_result.get('action')}")
                    action = trade_result.get("action", "")
                    if action in ("close", "reverse") and self._open_trade_memory_id is not None:
                        memory_service.update_outcome(self._open_trade_memory_id, trade_result.get("pnl", 0))
                        self._open_trade_memory_id = None

            # 8. 持久化 + 事件推送
            await persist_tick(price, account, position, signal, trade_result)
            await cache_signal(signal)
            await publish_event({
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

            cb_result = await self.risk.record_tick_success()
            if cb_result.get("action") == "cleared":
                logger.info(f"连续 {cb_result['success_count']} 次成功，熔断已自动解除")

            from app.agents.agent_status import save_tick_agent_logs
            await save_tick_agent_logs(
                self.agent_mode_display,
                signal=signal.signal, confidence=signal.confidence,
                reason=signal.reason, stop_loss=signal.stop_loss,
                take_profit=signal.take_profit, source_count=signal.source_count,
            )

        except Exception as e:
            err_name = type(e).__name__
            logger.error(f"Tick 异常: {err_name}: {e}")
            cb_result = await self.risk.record_tick_failure(err_name)
            if cb_result.get("action") == "paused":
                logger.warning(f"连续 {cb_result['fail_count']} 次失败，暂停 {cb_result['pause_minutes']} 分钟")
            elif cb_result.get("action") == "stopped":
                logger.critical(f"连续 {cb_result['fail_count']} 次失败，熔断停引擎！请人工检查后手动重启")
                await self.risk.trip_circuit_breaker(
                    f"连续 {cb_result['fail_count']} 次 tick 失败 ({err_name})，引擎已停止"
                )
                await publish_event({
                    "type": "circuit_breaker",
                    "state": "stopped",
                    "reason": f"连续 {cb_result['fail_count']} 次失败，引擎已停止",
                })
