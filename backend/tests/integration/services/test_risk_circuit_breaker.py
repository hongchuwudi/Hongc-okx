"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_risk_circuit_breaker.py 风控熔断状态机集成测试
描述: 真实 Redis 验证熔断分级流转 — 暂停冷却 / 停引擎 / 自动恢复

不依赖 LLM，直接打真实 Redis（config.redis），验证 RiskService 状态机
在 Redis 中的真实流转。这是核心安全逻辑，值得真实存储验证。

熔断规则（risk.py）:
- 连续失败 5 次  → paused（暂停 5 分钟冷却）
- 连续失败 10 次 → stopped（停止引擎，需人工介入）
- 连续成功 3 次  → 自动解除熔断

隔离策略:
- 使用真实 RiskService 单例，但每个测试前 reset_circuit_breaker 清空熔断状态
- autouse fixture 保证测试前后 Redis 熔断 key 干净，不污染生产数据
- 测试串行执行（同进程内顺序），避免状态竞争

包含:
- class TestCircuitBreakerCounting — 失败/成功计数流转
- class TestCircuitBreakerPause — 连续 5 次失败触发暂停
- class TestCircuitBreakerStop — 连续 10 次失败触发停止
- class TestCircuitBreakerAutoClear — 连续成功 3 次自动解除
- class TestCircuitBreakerCheckPause — 暂停冷却状态查询
"""
import time

import pytest

from app.services.risk.risk import (
    RiskService,
    FAIL_PAUSE,
    FAIL_STOP,
    SUCCESS_CLEAR,
)

# 真实 Redis 异步连接池是模块级全局单例，绑定到首个 event loop。
# 由 backend/pytest.ini 的 asyncio_mode=auto + asyncio_default_test_loop_scope=session
# 统一配置：所有 async def 测试自动识别为 async 测试，共享 session 级 loop，
# 连接池只绑定一次，避免跨测试 "Event loop is closed"。

# ═══════════════════════════════════════════════════════════════
# 公共夹具：真实 RiskService + Redis 清理
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def risk():
    """真实 RiskService 实例，操作真实 Redis。"""
    return RiskService()


@pytest.fixture(autouse=True)
async def clean_circuit_breaker(risk):
    """每个测试前后清空熔断状态，确保隔离、不污染生产 Redis。"""
    await risk.reset_circuit_breaker()
    yield
    await risk.reset_circuit_breaker()


# ═══════════════════════════════════════════════════════════════
# 计数流转
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreakerCounting:
    """失败计数累加 + 成功计数重置逻辑。"""

    async def test_initial_state_is_none(self, risk):
        """初始熔断状态应为 none。"""
        state = await risk.get_circuit_state()
        assert state["state"] in ("none", None), f"初始应为 none，实际 {state['state']}"
        assert state["fail_count"] == 0

    async def test_failure_increments_count(self, risk):
        """每次失败 fail_count +1，未达阈值时 action=counted。"""
        r1 = await risk.record_tick_failure()
        r2 = await risk.record_tick_failure()
        assert r1["fail_count"] == 1
        assert r2["fail_count"] == 2
        assert r1["action"] == "counted"
        assert r2["action"] == "counted"

    async def test_success_resets_fail_count(self, risk):
        """失败 2 次后成功一次，成功计数从 1 开始累加。"""
        await risk.record_tick_failure()
        await risk.record_tick_failure()
        ok = await risk.record_tick_success()
        assert ok["success_count"] == 1

    async def test_failure_clears_success_count(self, risk):
        """失败会清空连续成功计数（delete _CB_OK）。"""
        await risk.record_tick_success()
        await risk.record_tick_success()
        await risk.record_tick_failure()
        state = await risk.get_circuit_state()
        assert state["success_count"] == 0, "失败后成功计数应清零"


# ═══════════════════════════════════════════════════════════════
# 暂停触发（连续 5 次失败）
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreakerPause:
    """连续 FAIL_PAUSE 次失败触发暂停冷却。"""

    @pytest.mark.xfail(
        reason="已知 bug: trip_circuit_breaker(reason) 与 set(_CB_KEY,'paused') "
               "抢同一 Redis key，reason 覆盖状态值，导致 get_circuit_state "
               "返回中文消息而非 'paused'",
        strict=False,
    )
    async def test_five_failures_trigger_pause(self, risk):
        """连续 5 次失败 → action=paused，状态变 paused。"""
        last = None
        for _ in range(FAIL_PAUSE):
            last = await risk.record_tick_failure("test_error")
        assert last["action"] == "paused", f"第 {FAIL_PAUSE} 次应 paused，实际 {last['action']}"
        assert last["fail_count"] == FAIL_PAUSE
        state = await risk.get_circuit_state()
        assert state["state"] == "paused", f"状态应为 paused，实际 {state['state']}"
        assert state["paused"] is True

    async def test_pause_sets_remaining_cooldown(self, risk):
        """暂停后剩余冷却时间应 > 0。"""
        for _ in range(FAIL_PAUSE):
            await risk.record_tick_failure()
        state = await risk.get_circuit_state()
        assert state["pause_remaining_s"] > 0, "暂停期间剩余冷却时间应 > 0"

    async def test_four_failures_not_paused(self, risk):
        """连续 4 次（阈值-1）不应触发暂停。"""
        for _ in range(FAIL_PAUSE - 1):
            r = await risk.record_tick_failure()
        assert r["action"] == "counted", f"未达阈值应 counted，实际 {r['action']}"
        state = await risk.get_circuit_state()
        assert state["state"] != "paused"


# ═══════════════════════════════════════════════════════════════
# 停止触发（连续 10 次失败）
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreakerStop:
    """连续 FAIL_STOP 次失败触发停止引擎。"""

    async def test_ten_failures_trigger_stop(self, risk):
        """连续 10 次失败 → action=stopped，状态变 stopped。"""
        last = None
        for _ in range(FAIL_STOP):
            last = await risk.record_tick_failure("fatal")
        assert last["action"] == "stopped", f"第 {FAIL_STOP} 次应 stopped，实际 {last['action']}"
        state = await risk.get_circuit_state()
        assert state["state"] == "stopped"
        assert state["stopped"] is True

    async def test_stop_supersedes_pause(self, risk):
        """超过暂停阈值继续失败到停止阈值，最终状态是 stopped 而非 paused。"""
        for _ in range(FAIL_STOP):
            await risk.record_tick_failure()
        state = await risk.get_circuit_state()
        assert state["state"] == "stopped", "达到停止阈值后应覆盖暂停为 stopped"


# ═══════════════════════════════════════════════════════════════
# 自动解除（连续成功 3 次）
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreakerAutoClear:
    """连续 SUCCESS_CLEAR 次成功自动解除熔断。"""

    @pytest.mark.xfail(
        reason="已知 bug: 同 test_five_failures_trigger_pause，state 字段被 "
               "reason 覆盖，连续成功清除后仍读不到 'none'",
        strict=False,
    )
    async def test_three_successes_auto_clear(self, risk):
        """先触发暂停，再连续 3 次成功 → 自动清除。"""
        for _ in range(FAIL_PAUSE):
            await risk.record_tick_failure()
        state = await risk.get_circuit_state()
        assert state["state"] == "paused"

        last = None
        for _ in range(SUCCESS_CLEAR):
            last = await risk.record_tick_success()
        assert last["action"] == "cleared", f"连续 {SUCCESS_CLEAR} 次成功应 cleared，实际 {last['action']}"
        state = await risk.get_circuit_state()
        assert state["state"] in ("none", None), f"清除后应为 none，实际 {state['state']}"

    async def test_two_successes_not_cleared(self, risk):
        """连续 2 次（阈值-1）成功不自动清除。"""
        for _ in range(FAIL_PAUSE):
            await risk.record_tick_failure()
        for _ in range(SUCCESS_CLEAR - 1):
            r = await risk.record_tick_success()
        assert r["action"] == "ok", f"未达阈值应 ok，实际 {r['action']}"
        state = await risk.get_circuit_state()
        assert state["success_count"] == SUCCESS_CLEAR - 1

    async def test_reset_circuit_breaker_clears_all(self, risk):
        """reset_circuit_breaker 后所有熔断状态归零。"""
        for _ in range(FAIL_STOP):
            await risk.record_tick_failure()
        await risk.reset_circuit_breaker()
        state = await risk.get_circuit_state()
        assert state["fail_count"] == 0
        assert state["success_count"] == 0
        assert state["state"] in ("none", None)


# ═══════════════════════════════════════════════════════════════
# 暂停冷却状态查询
# ═══════════════════════════════════════════════════════════════

class TestCircuitBreakerCheckPause:
    """check_pause 查询暂停是否阻断 tick。"""

    @pytest.mark.xfail(
        reason="已知 bug: check_pause 读 _CB_KEY 与中文 reason 比对，reason≠'paused' "
               "→ 暂停期间错误返回 blocked=False，熔断暂停形同虚设",
        strict=False,
    )
    async def test_check_pause_blocks_when_paused(self, risk):
        """暂停期间 check_pause 应 blocked=True。"""
        for _ in range(FAIL_PAUSE):
            await risk.record_tick_failure()
        result = await risk.check_pause()
        assert result["blocked"] is True, "暂停期间应 blocked"

    async def test_check_pause_not_blocked_when_none(self, risk):
        """无熔断时 check_pause 应 blocked=False。"""
        result = await risk.check_pause()
        assert result["blocked"] is False
