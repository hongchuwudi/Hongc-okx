"""
创建时间: 2026-06-16
作者: hongchuwudi
描述: RuntimeSyncMixin — 运行时配置同步（从 Redis 读取并热切换）

包含:
- 类: RuntimeSyncMixin — 提供 _sync_runtime() 方法的混入类
"""

from app.services.agent.agent_coordinator_service import (
    create_coordinator, create_coordinator_3, create_coordinator_solo,
    create_position_manager,
)
from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

logger = get_logger()


class RuntimeSyncMixin:
    """混入类 — 提供 _sync_runtime() 方法，供 TradingEngine 继承。

    要求宿主类 __init__ 中必须初始化以下属性：
    - self._last_mode, self._last_symbol, self._last_leverage, self._last_prompt_version
    - self.use_multi_agent, self.agent_mode_display, self.coordinator
    - self.exchange, self.market_data, self.scheduler
    - self._symbol, self.position_manager
    """

    async def _sync_runtime(self) -> None:
        """读取 Redis 运行时配置，检测变化并热切换。"""

        # --- agent_mode: 热切换 coordinator ---
        mode = await get_runtime_async("agent_mode")
        if mode != self._last_mode or self.coordinator is None:
            self._last_mode = mode
            if mode == "tech":
                self.use_multi_agent = False
                self.agent_mode_display = "技术指标 (纯规则)"
                self.coordinator = None
                logger.info("[运行时] 切换模式 → 技术指标")
            elif mode == "1_agent":
                self.coordinator = create_coordinator_solo()
                self.use_multi_agent = True
                self.agent_mode_display = "1 Agent Solo (急速)"
                logger.info("[运行时] 切换模式 → 1 Agent Solo")
            elif mode == "3_agent":
                self.coordinator = create_coordinator_3()
                self.use_multi_agent = True
                self.agent_mode_display = "3 Agent Swarm (快速)"
                logger.info("[运行时] 切换模式 → 3 Agent")
            else:
                self.coordinator = create_coordinator()
                self.use_multi_agent = True
                self.agent_mode_display = "5 Agent Swarm (完整)"
                logger.info("[运行时] 切换模式 → 5 Agent")

        # --- 提示词热重载: Redis 版本变化 → 重建 coordinator ---
        if self.use_multi_agent and self.coordinator is not None:
            try:
                from app.agents.prompts import get_prompt_version
                pv = await get_prompt_version()
                if pv != self._last_prompt_version:
                    self._last_prompt_version = pv
                    logger.info("[运行时] 检测到提示词变更，重建 Agent...")
                    if mode == "1_agent":
                        self.coordinator = create_coordinator_solo()
                    elif mode == "3_agent":
                        self.coordinator = create_coordinator_3()
                    else:
                        self.coordinator = create_coordinator()
                    logger.info("[运行时] Agent 已热重载")
            except Exception:
                pass

        # --- symbol: 仅无持仓时可切换 ---
        new_symbol = await get_runtime_async("symbol")
        if new_symbol != self._last_symbol:
            self._last_symbol = new_symbol
            try:
                pos = await self.market_data.get_positions(self._symbol)
                if pos and pos.get("side") and pos.get("size", 0) > 0:
                    logger.warning(f"[运行时] 有持仓，交易对切换暂缓: {self._symbol} → {new_symbol}")
                elif new_symbol != self._symbol:
                    self._symbol = new_symbol
                    self.position_manager = create_position_manager(self.exchange, new_symbol)
                    logger.info(f"[运行时] 交易对切换 → {new_symbol}")
            except Exception:
                if new_symbol != self._symbol:
                    self._symbol = new_symbol
                    self.position_manager = create_position_manager(self.exchange, new_symbol)

        # --- leverage: 仅无持仓时可切换 ---
        new_lev = int(await get_runtime_async("leverage"))
        if new_lev != self._last_leverage:
            self._last_leverage = new_lev
            try:
                pos = await self.market_data.get_positions(self._symbol)
                if pos and pos.get("side") and pos.get("size", 0) > 0:
                    logger.warning(f"[运行时] 有持仓，杠杆切换暂缓 → {new_lev}x")
                else:
                    await self.exchange.set_leverage(self._symbol, new_lev)
                    logger.info(f"[运行时] 杠杆切换 → {new_lev}x")
            except Exception as e:
                logger.warning(f"[运行时] 杠杆切换失败: {e}")

        # --- tick_interval: 动态更新调度器间隔 ---
        new_interval = int(await get_runtime_async("tick_interval_seconds"))
        if new_interval != self.scheduler._interval:
            self.scheduler._interval = new_interval
            logger.info(f"[运行时] Tick 间隔切换 → {new_interval}s")
