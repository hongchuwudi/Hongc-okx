"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: risk.py 中文名
描述: 风控服务 — 智能熔断 + 仓位上限 + 回撤熔断 + 日亏损限额等多层次风险控制

包含:
- 类: RiskResult — 风控检查结果数据类
- 类: RiskService — 全局风控服务，实现多级检查链 + 分级熔断
- 常量: FAIL_PAUSE — 触发暂停的连续失败次数
- 常量: FAIL_STOP — 触发停引擎的连续失败次数
- 常量: SUCCESS_CLEAR — 连续成功次数以自动解除熔断
- 常量: PAUSE_MINUTES — 暂停冷却时间（分钟）
"""

import time
from dataclasses import dataclass
from datetime import datetime

from app.core.config import config
from app.core.database import get_redis
from app.services.config.runtime import get_runtime

# 熔断阈值
FAIL_PAUSE = 5       # 连续失败 N 次 → 暂停冷却
FAIL_STOP = 10       # 连续失败 N 次 → 停止引擎
SUCCESS_CLEAR = 3    # 连续成功 N 次 → 自动解除
PAUSE_MINUTES = 5    # 暂停冷却时间（分钟）

# Redis key 前缀
_CB_KEY = "risk:circuit_breaker"       # 熔断状态: none | paused | stopped
_CB_FAIL = "risk:cb_fail_count"        # 连续失败计数
_CB_OK = "risk:cb_success_count"       # 连续成功计数
_CB_PAUSE = "risk:cb_pause_until"      # 暂停到期时间戳


@dataclass
class RiskResult:
    passed: bool                    # 是否通过检查
    reason: str = ""                # 未通过的原因描述
    blocked_by: str = ""            # 触发拦截的检查项名称


class RiskService:

    def __init__(self):
        self._daily_peak_equity: float | None = None
        self._daily_loss: float = 0.0
        self._last_trade_time: datetime | None = None
        self._circuit_breaker_reason: str = ""
        self._daily_date: str = ""

    # ── 智能熔断（分级：暂停冷却 / 停引擎 / 自动恢复）──

    async def get_circuit_state(self) -> dict:
        """返回当前熔断状态。"""
        redis = await get_redis()
        state = await redis.get(_CB_KEY) or "none"
        fail = int(await redis.get(_CB_FAIL) or 0)
        ok = int(await redis.get(_CB_OK) or 0)
        pause_until = float(await redis.get(_CB_PAUSE) or 0)
        remaining = max(0, pause_until - time.time())
        return {
            "state": state,              # none | paused | stopped
            "fail_count": fail,
            "success_count": ok,
            "paused": state == "paused",
            "stopped": state == "stopped",
            "pause_remaining_s": int(remaining),
        }

    async def record_tick_success(self) -> dict:
        """记录一次成功的 tick，连续成功达阈值则自动解除熔断。"""
        redis = await get_redis()
        ok = await redis.incr(_CB_OK)
        await redis.expire(_CB_OK, 3600)
        # 连续成功 SUCCESS_CLEAR 次 → 自动解除
        if ok >= SUCCESS_CLEAR:
            await self.reset_circuit_breaker()
            return {"action": "cleared", "success_count": ok}
        return {"action": "ok", "success_count": ok}

    async def record_tick_failure(self, error_type: str = "") -> dict:
        """
        记录一次失败的 tick。
        5 次 → 暂停 5 分钟（冷却后自动恢复）
        10 次 → 停止引擎（需人工介入）
        """
        redis = await get_redis()
        # 重置连续成功计数
        await redis.delete(_CB_OK)
        fail = await redis.incr(_CB_FAIL)
        await redis.expire(_CB_FAIL, 7200)

        if fail >= FAIL_STOP:
            await self.trip_circuit_breaker(
                f"连续 {fail} 次 tick 失败 ({error_type})，引擎已停止，需人工介入"
            )
            await redis.set(_CB_KEY, "stopped")
            return {"action": "stopped", "fail_count": fail}

        if fail >= FAIL_PAUSE:
            pause_until = time.time() + PAUSE_MINUTES * 60
            await redis.set(_CB_KEY, "paused")
            await redis.set(_CB_PAUSE, str(pause_until))
            await redis.expire(_CB_PAUSE, PAUSE_MINUTES * 60 + 60)
            await self.trip_circuit_breaker(
                f"连续 {fail} 次 tick 失败 ({error_type})，暂停 {PAUSE_MINUTES} 分钟冷却"
            )
            return {"action": "paused", "fail_count": fail, "pause_minutes": PAUSE_MINUTES}

        return {"action": "counted", "fail_count": fail}

    async def check_pause(self) -> dict:
        """
        检查暂停状态是否已冷却完毕。
        Returns: {"blocked": True/False, "remaining_s": int}
        """
        redis = await get_redis()
        state = await redis.get(_CB_KEY) or "none"
        if state != "paused":
            return {"blocked": False, "remaining_s": 0}

        pause_until = float(await redis.get(_CB_PAUSE) or 0)
        remaining = max(0, pause_until - time.time())
        if remaining <= 0:
            # 冷却完毕，降级为监控状态（保留失败计数，不清除）
            await redis.set(_CB_KEY, "none")
            await redis.delete(_CB_KEY)  # 清除旧的熔断消息
            return {"blocked": False, "remaining_s": 0, "resumed": True}

        return {"blocked": True, "remaining_s": int(remaining)}

    # ── 完整风控检查链 ──────────────────────────────────

    async def check(
        self, signal: str, equity: float, current_position_value: float = 0
    ) -> RiskResult:
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
        redis = await get_redis()
        val = await redis.get(_CB_KEY)
        if val and val != "none":
            return False, f"熔断已触发[{val}]: {await redis.get('risk:circuit_breaker') or ''}"
        return True, ""

    def _check_drawdown(self, equity: float) -> tuple[bool, str]:
        today = datetime.now().strftime("%Y%m%d")
        if self._daily_date != today:
            self._daily_peak_equity = None
            self._daily_loss = 0.0
            self._daily_date = today
        if self._daily_peak_equity is None:
            self._daily_peak_equity = equity
        else:
            self._daily_peak_equity = max(self._daily_peak_equity, equity)
        if self._daily_peak_equity > 0:
            dd = (self._daily_peak_equity - equity) / self._daily_peak_equity * 100
            max_dd = get_runtime("max_daily_drawdown_pct")
            if dd > max_dd:
                return False, f"回撤 {dd:.1f}% > {max_dd}%"
        return True, ""

    def _check_daily_loss(self) -> tuple[bool, str]:
        max_loss = get_runtime("max_daily_loss_usdt")
        if self._daily_loss >= max_loss:
            return False, f"日亏损 ${self._daily_loss:.0f} >= ${max_loss:.0f}"
        return True, ""

    def _check_position_limit(
        self, equity: float, current_value: float, signal: str
    ) -> tuple[bool, str]:
        if signal == "HOLD":
            return True, ""
        max_allowed = equity * get_runtime("max_position_ratio")
        if current_value >= max_allowed:
            return False, f"仓位 ${current_value:.0f} >= 上限 ${max_allowed:.0f}"
        return True, ""

    async def _check_trade_frequency(self) -> tuple[bool, str]:
        redis = await get_redis()
        last_ts = await redis.get("risk:last_trade_time")
        if last_ts:
            elapsed = time.time() - float(last_ts)
            if elapsed < 300:
                return False, f"开仓过快 (距上次 {elapsed:.0f}s)"
        return True, ""

    # ── 外部操作 ─────────────────────────────────────────────

    async def trip_circuit_breaker(self, reason: str) -> None:
        redis = await get_redis()
        await redis.set("risk:circuit_breaker", reason)
        self._circuit_breaker_reason = reason

    async def reset_circuit_breaker(self) -> None:
        """重置所有熔断状态。"""
        redis = await get_redis()
        await redis.delete("risk:circuit_breaker")
        await redis.delete(_CB_KEY)
        await redis.delete(_CB_FAIL)
        await redis.delete(_CB_OK)
        await redis.delete(_CB_PAUSE)
        self._circuit_breaker_reason = ""

    async def record_trade(self, pnl: float) -> None:
        redis = await get_redis()
        await redis.set("risk:last_trade_time", str(time.time()))
        if pnl < 0:
            self._daily_loss += abs(pnl)

    def reset_daily(self) -> None:
        self._daily_peak_equity = None
        self._daily_loss = 0.0


# 模块级单例，供 API 端点调用
risk_service = RiskService()
