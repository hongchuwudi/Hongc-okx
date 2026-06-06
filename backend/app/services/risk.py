"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: risk.py 中文名
描述: 风控服务 — 仓位上限、回撤熔断、日亏损限额等多层次风险控制

包含:
- 类: RiskResult — 风控检查结果数据类
- 类: RiskService — 全局风控服务，实现多级检查链
"""

import time
from dataclasses import dataclass
from datetime import datetime

from app.config import config
from app.database import get_redis


@dataclass
class RiskResult:
    """风控检查结果"""
    passed: bool                    # 是否通过检查
    reason: str = ""                # 未通过的原因描述
    blocked_by: str = ""            # 触发拦截的检查项名称


class RiskService:
    """全局风控服务

    检查链（按优先级）:
    1. 熔断开关 (Redis)
    2. 最大日回撤
    3. 日亏损限额
    4. 全局仓位上限
    5. 开仓频率限制
    """

    def __init__(self):
        # 当日峰值权益（用于计算回撤）
        self._daily_peak_equity: float | None = None
        # 当日累计亏损
        self._daily_loss: float = 0.0
        # 上次交易时间
        self._last_trade_time: datetime | None = None
        # 熔断原因
        self._circuit_breaker_reason: str = ""
        # 当前日期字符串，用于跨天重置
        self._daily_date: str = ""

    async def check(
        self, signal: str, equity: float, current_position_value: float = 0
    ) -> RiskResult:
        """执行完整风控检查链"""
        checks = [
            ("熔断开关", await self._check_circuit_breaker()),
            ("日回撤", self._check_drawdown(equity)),
            ("日亏损", self._check_daily_loss()),
            ("仓位上限", self._check_position_limit(equity, current_position_value, signal)),
            ("开仓频率", await self._check_trade_frequency()),
        ]
        for name, (passed, reason) in checks:
            if not passed:
                return RiskResult(passed=False, reason=f"[{name}] {reason}", blocked_by=name)
        return RiskResult(passed=True)

    # ── 单项检查 ─────────────────────────────────────────────

    async def _check_circuit_breaker(self) -> tuple[bool, str]:
        """检查 Redis 中的熔断开关是否已触发"""
        redis = await get_redis()
        val = await redis.get("risk:circuit_breaker")
        if val:
            return False, f"熔断已触发: {val}"
        return True, ""

    def _check_drawdown(self, equity: float) -> tuple[bool, str]:
        """检查当日回撤是否超过最大允许比例"""
        today = datetime.now().strftime("%Y%m%d")
        # 跨天时重置日统计
        if self._daily_date != today:
            self._daily_peak_equity = None
            self._daily_loss = 0.0
            self._daily_date = today
        # 更新当日峰值
        if self._daily_peak_equity is None:
            self._daily_peak_equity = equity
        else:
            self._daily_peak_equity = max(self._daily_peak_equity, equity)
        # 计算回撤百分比
        if self._daily_peak_equity > 0:
            dd = (self._daily_peak_equity - equity) / self._daily_peak_equity * 100
            if dd > config.trade.max_daily_drawdown_pct:
                return False, f"回撤 {dd:.1f}% > {config.trade.max_daily_drawdown_pct}%"
        return True, ""

    def _check_daily_loss(self) -> tuple[bool, str]:
        """检查当日累计亏损是否超过限制"""
        if self._daily_loss >= config.trade.max_daily_loss_usdt:
            return False, f"日亏损 ${self._daily_loss:.0f} >= ${config.trade.max_daily_loss_usdt:.0f}"
        return True, ""

    def _check_position_limit(
        self, equity: float, current_value: float, signal: str
    ) -> tuple[bool, str]:
        """检查当前仓位是否超过允许的最大仓位比例"""
        if signal == "HOLD":
            return True, ""
        max_allowed = equity * config.trade.max_position_ratio
        if current_value >= max_allowed:
            return False, f"仓位 ${current_value:.0f} >= 上限 ${max_allowed:.0f}"
        return True, ""

    async def _check_trade_frequency(self) -> tuple[bool, str]:
        """检查开仓频率，防止过于频繁交易"""
        redis = await get_redis()
        last_ts = await redis.get("risk:last_trade_time")
        if last_ts:
            elapsed = time.time() - float(last_ts)
            # 距上次交易不足 300 秒则拦截
            if elapsed < 300:
                return False, f"开仓过快 (距上次 {elapsed:.0f}s)"
        return True, ""

    # ── 外部操作 ─────────────────────────────────────────────

    async def trip_circuit_breaker(self, reason: str) -> None:
        """触发熔断开关，停止一切交易"""
        redis = await get_redis()
        await redis.set("risk:circuit_breaker", reason)
        self._circuit_breaker_reason = reason

    async def reset_circuit_breaker(self) -> None:
        """重置熔断开关，恢复交易"""
        redis = await get_redis()
        await redis.delete("risk:circuit_breaker")
        self._circuit_breaker_reason = ""

    async def record_trade(self, pnl: float) -> None:
        """记录一笔交易，更新日亏损和交易频率"""
        redis = await get_redis()
        await redis.set("risk:last_trade_time", str(time.time()))
        if pnl < 0:
            self._daily_loss += abs(pnl)

    def reset_daily(self) -> None:
        """每日重置（建议在 UTC 0 点调用）"""
        self._daily_peak_equity = None
        self._daily_loss = 0.0
