"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: test_runtime_config.py 运行时配置集成测试
描述: 真实 Redis 验证 runtime 配置读写循环 + 类型转换 + 来源识别

不依赖 LLM，runtime 用同步 Redis 客户端（redis.Redis.from_url），不走异步
连接池，无 event loop 跨测试问题。纯同步测试。

验证契约:
- set_runtime / get_runtime 往返一致（含 int/float/bool/str 类型转换）
- get_all_runtime 返回全部 key 且类型正确
- get_runtime_sources 正确区分 redis / env 来源
- delete_runtime 删除后回退到 env 默认值
- sync_runtime_to_env 把 Redis 值持久化到 .env（用临时副本，绝不碰真实 .env）

隔离策略:
- 使用真实 Redis hash key trading:runtime_config，每个测试前后清理该 hash
- sync_runtime_to_env 测试在临时 .env 副本上运行，通过 monkeypatch 替换路径

包含:
- class TestRuntimeRoundTrip — 单 key 读写往返 + 类型转换
- class TestRuntimeBatchAndAll — 批量写入 + 全量读取
- class TestRuntimeSources — 来源识别（redis / env）
- class TestRuntimeDelete — 删除回退 env
- class TestSyncRuntimeToEnv — .env 持久化（临时副本隔离）
"""
import os
from pathlib import Path

import pytest

from app.services.config.runtime import (
    REDIS_KEY,
    get_runtime,
    set_runtime,
    set_runtime_batch,
    get_all_runtime,
    get_runtime_sources,
    delete_runtime,
    sync_runtime_to_env,
)


# ═══════════════════════════════════════════════════════════════
# 公共夹具：清理 Redis runtime hash
# ═══════════════════════════════════════════════════════════════

def _clear_runtime_hash():
    """同步清空 Redis 中的 runtime 配置 hash，确保测试隔离。"""
    import redis
    from app.core.config import config
    r = redis.Redis.from_url(config.redis.url, decode_responses=True)
    r.delete(REDIS_KEY)


@pytest.fixture(autouse=True)
def clean_runtime():
    """每个测试前后清空 Redis runtime hash，不污染生产配置。"""
    _clear_runtime_hash()
    yield
    _clear_runtime_hash()


# ═══════════════════════════════════════════════════════════════
# 单 key 读写往返 + 类型转换
# ═══════════════════════════════════════════════════════════════

class TestRuntimeRoundTrip:
    """set/get 往返一致，类型转换正确。"""

    def test_int_round_trip(self):
        set_runtime("leverage", 20)
        assert get_runtime("leverage") == 20
        assert isinstance(get_runtime("leverage"), int)

    def test_float_round_trip(self):
        set_runtime("order_amount", 2.5)
        assert get_runtime("order_amount") == 2.5
        assert isinstance(get_runtime("order_amount"), float)

    def test_bool_round_trip(self):
        set_runtime("sandbox", False)
        assert get_runtime("sandbox") is False
        set_runtime("sandbox", True)
        assert get_runtime("sandbox") is True

    def test_str_round_trip(self):
        set_runtime("symbol", "ETH/USDT:USDT")
        assert get_runtime("symbol") == "ETH/USDT:USDT"

    def test_get_uninitialized_falls_back_to_env(self):
        """未 set 的 key 应回退 env 默认值，且类型正确。"""
        val = get_runtime("data_points")
        assert isinstance(val, int)
        assert val > 0

    def test_set_overwrites_previous(self):
        set_runtime("leverage", 5)
        set_runtime("leverage", 15)
        assert get_runtime("leverage") == 15


# ═══════════════════════════════════════════════════════════════
# 批量写入 + 全量读取
# ═══════════════════════════════════════════════════════════════

class TestRuntimeBatchAndAll:
    """批量写入 + 全量读取。"""

    def test_batch_set_multiple_keys(self):
        set_runtime_batch({
            "leverage": 25,
            "symbol": "BTC/USDT:USDT",
            "sandbox": False,
        })
        assert get_runtime("leverage") == 25
        assert get_runtime("symbol") == "BTC/USDT:USDT"
        assert get_runtime("sandbox") is False

    def test_batch_ignores_unknown_keys(self):
        """未知 key 应被静默忽略，不抛异常。"""
        set_runtime_batch({"leverage": 10, "unknown_key": "value"})
        assert get_runtime("leverage") == 10

    def test_get_all_returns_all_keys(self):
        """get_all_runtime 应返回 _TYPE_MAP 中全部 key。"""
        from app.services.config.runtime import _TYPE_MAP
        all_rt = get_all_runtime()
        assert set(all_rt.keys()) == set(_TYPE_MAP.keys())

    def test_get_all_types_correct(self):
        """get_all_runtime 每个值类型与 _TYPE_MAP 声明一致。"""
        from app.services.config.runtime import _TYPE_MAP
        all_rt = get_all_runtime()
        for key, (conv, _default) in _TYPE_MAP.items():
            assert isinstance(all_rt[key], conv), (
                f"{key}: 期望 {conv.__name__}，实际 {type(all_rt[key]).__name__}"
            )


# ═══════════════════════════════════════════════════════════════
# 来源识别
# ═══════════════════════════════════════════════════════════════

class TestRuntimeSources:
    """get_runtime_sources 区分 redis / env 来源。"""

    def test_unset_key_source_is_env(self):
        sources = get_runtime_sources()
        assert sources["leverage"]["source"] == "env"

    def test_set_key_source_is_redis(self):
        set_runtime("leverage", 30)
        sources = get_runtime_sources()
        assert sources["leverage"]["source"] == "redis"
        assert sources["leverage"]["value"] == 30

    def test_sources_covers_all_keys(self):
        from app.services.config.runtime import _TYPE_MAP
        sources = get_runtime_sources()
        assert set(sources.keys()) == set(_TYPE_MAP.keys())
        for key, info in sources.items():
            assert info["source"] in ("redis", "env"), f"{key}: {info['source']}"


# ═══════════════════════════════════════════════════════════════
# 删除回退 env
# ═══════════════════════════════════════════════════════════════

class TestRuntimeDelete:
    """delete_runtime 后回退 env 默认值。"""

    def test_delete_restores_env_default(self):
        set_runtime("leverage", 99)
        assert get_runtime("leverage") == 99
        delete_runtime("leverage")
        sources = get_runtime_sources()
        assert sources["leverage"]["source"] == "env"

    def test_delete_unset_key_no_error(self):
        """删除从未设置的 key 不应抛异常。"""
        delete_runtime("leverage")  # 不应 raise


# ═══════════════════════════════════════════════════════════════
# .env 持久化（临时副本隔离）
# ═══════════════════════════════════════════════════════════════

class _FakePath:
    """假 Path 对象，链式 resolve/parent/truediv 最终指向目标 .env 文件。

    sync_runtime_to_env 内部计算:
      pathlib.Path(__file__).resolve().parent.parent.parent.parent / ".env"
    用 _FakePath 替换 pathlib.Path，无论链多长都返回固定目标路径，
    使 sync 写入临时文件而非真实 backend/.env。
    """

    def __init__(self, target: Path):
        self._target = target

    def resolve(self):
        return self

    @property
    def parent(self):
        return self

    def __truediv__(self, other):
        return self._target if other == ".env" else self

    def exists(self):
        return self._target.exists()

    def read_text(self, encoding="utf-8"):
        return self._target.read_text(encoding=encoding)

    def write_text(self, content, encoding="utf-8"):
        return self._target.write_text(content, encoding=encoding)


class TestSyncRuntimeToEnv:
    """sync_runtime_to_env 把 Redis 值写入 .env。

    安全隔离：通过 monkeypatch 替换 runtime 模块的 pathlib.Path 为 _FakePath，
    使 sync_runtime_to_env 读写临时 .env，绝不触碰真实 backend/.env。
    测试的是真实的 sync_runtime_to_env 函数逻辑。
    """

    def test_sync_writes_redis_value_to_env(self, tmp_path, monkeypatch):
        """Redis 改了 leverage，sync 后应写入临时 .env。"""
        set_runtime("leverage", 33)
        env_file = tmp_path / ".env"
        env_file.write_text("TRADE_LEVERAGE=10\nTRADE_SYMBOL=DOGE/USDT:USDT\n", encoding="utf-8")
        monkeypatch.setattr(
            "app.services.config.runtime.pathlib.Path",
            lambda _f: _FakePath(env_file),
        )
        sync_runtime_to_env()
        content = env_file.read_text(encoding="utf-8")
        assert "TRADE_LEVERAGE=33" in content, f"应写入 33，实际: {content}"

    def test_sync_no_change_returns_none(self, tmp_path, monkeypatch):
        """所有 key 都已在 .env 且值与 Redis 一致时返回 None。"""
        from app.services.config.runtime import _ENV_VAR_MAP
        # 用 get_all_runtime 的当前值构造完整一致的 .env
        rt = get_all_runtime()
        lines = []
        for rt_key, (env_var, _comment) in _ENV_VAR_MAP.items():
            value = rt.get(rt_key)
            if value is None:
                continue
            new_val = str(value).lower() if isinstance(value, bool) else str(value)
            lines.append(f"{env_var}={new_val}")
        env_file = tmp_path / ".env"
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        monkeypatch.setattr(
            "app.services.config.runtime.pathlib.Path",
            lambda _f: _FakePath(env_file),
        )
        assert sync_runtime_to_env() is None, "全量一致时应无变更返回 None"

    def test_sync_appends_new_key(self, tmp_path, monkeypatch):
        """.env 中缺失的 key 应追加到文件末尾。"""
        set_runtime("max_daily_loss_usdt", 25.0)
        env_file = tmp_path / ".env"
        env_file.write_text("TRADE_LEVERAGE=10\n", encoding="utf-8")
        monkeypatch.setattr(
            "app.services.config.runtime.pathlib.Path",
            lambda _f: _FakePath(env_file),
        )
        sync_runtime_to_env()
        content = env_file.read_text(encoding="utf-8")
        assert "MAX_DAILY_LOSS_USDT=25.0" in content, (
            f"新 key 应追加，实际: {content}"
        )

    def test_sync_does_not_touch_real_env(self, tmp_path, monkeypatch):
        """确认 sync 操作临时文件，真实 backend/.env 内容不变。"""
        real_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
        before = real_env.read_text(encoding="utf-8") if real_env.exists() else ""

        set_runtime("leverage", 77)
        env_file = tmp_path / ".env"
        env_file.write_text("TRADE_LEVERAGE=10\n", encoding="utf-8")
        monkeypatch.setattr(
            "app.services.config.runtime.pathlib.Path",
            lambda _f: _FakePath(env_file),
        )
        sync_runtime_to_env()

        after = real_env.read_text(encoding="utf-8") if real_env.exists() else ""
        assert before == after, "真实 .env 不应被修改"
