"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: engine.py 交易引擎
描述: TradingEngine 类 — run() 启动引擎 + _tick() 编排 8 步流水线

Tick 步骤实现位于 loop/ 目录：
- loop/tick_circuit.py — step 0: 熔断检查
- loop/tick_emoji.py      — emoji 清洗工具
- loop/tick_market.py      — step 2: 行情获取
- loop/tick_strategy.py — step 3: 策略分析
- loop/tick_position.py — step 4: 动态持仓管理
- loop/tick_memory.py  — step 5: AI 决策记忆
- loop/tick_risk.py    — step 6: 风控检查
- loop/tick_trade.py   — step 7: 交易执行
- loop/tick_persist.py — step 8: 持久化 + 异常处理 (持久化逻辑下沉到 services/persistence/)

包含:
- 类: TradingEngine — 交易引擎，事件驱动的主循环
"""

from datetime import datetime

from app.core.config import config
from app.exchange.client import ExchangeClient
from app.engine.runtime import RuntimeSyncMixin
from app.services.market.market_data import MarketDataService
from app.services.risk.risk import RiskService
from app.services.engine.scheduler import SchedulerService
from app.services.trading.strategy import StrategyService
from app.services.trading.trade import TradeService
from app.services.agent.agent_coordinator_service import (
    create_position_manager, get_indicator_service,
)
from app.services.strategies.strategy_technical import TechnicalStrategy
from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

from app.engine.loop.tick_circuit import tick_check_circuit
from app.engine.loop.tick_market import tick_fetch_market
from app.engine.loop.tick_strategy import tick_analyze_strategy
from app.engine.loop.tick_position import tick_manage_position
from app.engine.loop.tick_memory import tick_record_memory
from app.engine.loop.tick_risk import tick_check_risk
from app.engine.loop.tick_trade import tick_execute_trade
from app.engine.loop.tick_persist import tick_persist_and_notify, tick_handle_error

IndicatorService = get_indicator_service()
logger = get_logger()


class TradingEngine(RuntimeSyncMixin):
    """交易引擎 — 事件驱动的主循环，协调行情、策略、风控、交易、持久化全流程。"""

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
        """启动交易引擎：设置交易所参数 → 同步配置 → 进入主循环。"""
        self._last_symbol = self._symbol

        try:
            await self.exchange.set_position_mode(hedged=False)
            logger.info("持仓模式: 单向")
        except Exception as e:
            from app.exchange.base import parse_okx_error
            logger.warning(f"持仓模式设置跳过: {parse_okx_error(e)}")

        try:
            leverage_val = int(await get_runtime_async("leverage"))
            await self.exchange.set_leverage(self._symbol, leverage_val)
            self._last_leverage = leverage_val
            logger.info(f"杠杆: {leverage_val}x")
        except Exception as e:
            from app.exchange.base import parse_okx_error
            logger.warning(f"杠杆设置跳过: {parse_okx_error(e)}")

        await self._sync_runtime()

        logger.info("=" * 50)
        logger.info("交易引擎启动")
        logger.info(f"交易对: {self._symbol}")
        logger.info(f"模式: {self.agent_mode_display}")
        logger.info("=" * 50)

        await self.risk.reset_circuit_breaker()
        logger.info("已重置熔断状态")

        await self.scheduler.run_loop(self._tick)

    # ── 单个交易周期（编排器）───────────────────────────

    async def _tick(self) -> None:
        """单个交易周期：熔断检查 → 8 步流水线 → 异常处理。"""
        tick_start = datetime.now()
        logger.info(f"--- Tick {tick_start.strftime('%H:%M:%S')} ---")

        # 0. 智能熔断：暂停冷却 / 已停止则跳过
        if not await tick_check_circuit(self):
            return
        try:
            # 1. 同步运行时配置
            await self._sync_runtime()
            # 2. 获取市场数据
            df, price, account, position = await tick_fetch_market(self)
            # 3. 策略分析
            signal, decision = await tick_analyze_strategy(self, df, price, account, position,)
            # 4. 动态持仓管理
            signal = await tick_manage_position(self, position, price, df, signal, IndicatorService,)
            # 5. AI 决策记忆
            await tick_record_memory(self, df, price, signal)
            # 6. 风控检查
            if not await tick_check_risk(self, signal, account, position, price):
                return
            # 7. 执行交易
            trade_result = await tick_execute_trade(self, signal, price, decision)
            # 8. 持久化 + 推送
            await tick_persist_and_notify(self, tick_start, price, account, position, signal, trade_result,)
        except Exception as e:
            await tick_handle_error(self, e)
