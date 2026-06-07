"""
创建时间: 2026-06-14
作者: hongchuwudi
文件名: runtime_config.py 运行时配置服务
描述: Redis 运行时配置 — 前端可实时修改，引擎每 tick 读取

包含:
- 函数: get_runtime — 同步读取单个 key（Redis → env fallback）
- 函数: set_runtime — 同步写入单个 key
- 函数: set_runtime_batch — 批量同步写入
- 函数: get_all_runtime — 同步获取全部配置
- 函数: get_runtime_sources — 获取全部配置及其来源（Redis / env）
- 函数: sync_runtime_to_env — 将 Redis 运行时配置持久化回 .env 文件
- 函数: get_runtime_async — 异步读取（供引擎使用）
- 函数: delete_runtime — 删除 key，恢复 env 默认
"""

import json
import os
import pathlib

import redis

from app.config import config
from app.config.config_trade import TradeConfig

REDIS_KEY = "trading:runtime_config"

# 默认值映射（key → env 回退值 / 类型转换）
_TYPE_MAP = {
    "symbol": (str, os.getenv("TRADE_SYMBOL", "DOGE/USDT:USDT")),
    "leverage": (int, int(os.getenv("TRADE_LEVERAGE", "10"))),
    "timeframe": (str, os.getenv("TRADE_TIMEFRAME", "1m")),
    "data_points": (int, int(os.getenv("TRADE_DATA_POINTS", "200"))),
    "tick_interval_seconds": (int, int(os.getenv("TRADE_TICK_INTERVAL_SECONDS", "360"))),
    "order_amount": (float, float(os.getenv("TRADE_ORDER_AMOUNT", "1.0"))),
    "max_position_ratio": (float, float(os.getenv("TRADE_MAX_POSITION_RATIO", "0.8"))),
    "max_daily_drawdown_pct": (float, float(os.getenv("MAX_DAILY_DRAWDOWN_PCT", "10.0"))),
    "max_daily_loss_usdt": (float, float(os.getenv("MAX_DAILY_LOSS_USDT", "50.0"))),
    "agent_auto_start": (bool, os.getenv("AGENT_AUTO_START", "true").lower() in ("true", "1", "yes")),
    "agent_mode": (str, os.getenv("AGENT_MODE", "5_agent")),  # "5_agent" | "3_agent" | "1_agent" | "tech"
    "sandbox": (bool, os.getenv("OKX_SANDBOX", "true").lower() == "true"),
}

_DEFAULTS = {k: v[1] for k, v in _TYPE_MAP.items()}

# runtime key → .env 变量名 + 注释 + 所属区块
_ENV_VAR_MAP = {
    "symbol":                    ("TRADE_SYMBOL",               "交易对符号"),
    "leverage":                  ("TRADE_LEVERAGE",             "杠杆倍数"),
    "timeframe":                 ("TRADE_TIMEFRAME",            "K线周期"),
    "data_points":               ("TRADE_DATA_POINTS",          "K线数据点数"),
    "tick_interval_seconds":     ("TRADE_TICK_INTERVAL_SECONDS","Tick 间隔（秒）"),
    "order_amount":              ("TRADE_ORDER_AMOUNT",         "单次下单金额（USDT）"),
    "max_position_ratio":        ("TRADE_MAX_POSITION_RATIO",   "最大仓位比例"),
    "max_daily_drawdown_pct":    ("MAX_DAILY_DRAWDOWN_PCT",     "最大日回撤百分比"),
    "max_daily_loss_usdt":       ("MAX_DAILY_LOSS_USDT",        "最大日亏损（USDT）"),
    "agent_auto_start":          ("AGENT_AUTO_START",           "Agent 自动启动"),
    "agent_mode":                ("AGENT_MODE",                 "Agent 模式"),
    "sandbox":                   ("OKX_SANDBOX",                "模拟盘开关"),
}


def _cast(key: str, raw: str):
    """将 Redis 中 json.dumps 存储的值解码为对应类型。"""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        conv, default = _TYPE_MAP[key]
        return default


def _sync_redis():
    """获取同步 Redis 客户端。"""
    return redis.Redis.from_url(config.redis.url, decode_responses=True)


# ── 同步方法（API 调用）─────────────────────────────────

def get_runtime(key: str):
    """读取运行时配置，Redis 优先。未命中则从 env 取值并回写 Redis。"""
    conv, default = _TYPE_MAP[key]
    try:
        r = _sync_redis()
        raw = r.hget(REDIS_KEY, key)
        if raw is not None:
            return _cast(key, raw)
        # Redis 未命中 → 用 env 默认值回写，下次直接命中
        r.hset(REDIS_KEY, key, json.dumps(default))
    except Exception:
        pass
    return default


def set_runtime(key: str, value) -> None:
    """写入单个运行时配置到 Redis。"""
    conv, _ = _TYPE_MAP[key]
    try:
        r = _sync_redis()
        r.hset(REDIS_KEY, key, json.dumps(conv(value)))
    except Exception:
        pass


def set_runtime_batch(updates: dict) -> None:
    """批量写入运行时配置到 Redis。"""
    try:
        r = _sync_redis()
        mapping = {}
        for k, v in updates.items():
            if k in _TYPE_MAP:
                conv, _ = _TYPE_MAP[k]
                mapping[k] = json.dumps(conv(v))
        if mapping:
            r.hset(REDIS_KEY, mapping=mapping)
    except Exception:
        pass


def get_all_runtime() -> dict:
    """获取全部运行时配置（Redis 值覆盖默认值）。"""
    result = dict(_DEFAULTS)
    try:
        r = _sync_redis()
        raw = r.hgetall(REDIS_KEY)
        for k, v in raw.items():
            if k in _TYPE_MAP:
                result[k] = _cast(k, v)
    except Exception:
        pass
    return result


def delete_runtime(key: str) -> None:
    """删除 Redis 中的运行时配置，恢复 env 默认值。"""
    try:
        r = _sync_redis()
        r.hdel(REDIS_KEY, key)
    except Exception:
        pass


def get_runtime_sources() -> dict:
    """
    获取全部运行时配置及其来源。
    Returns: { key: { "value": ..., "source": "redis" | "env" } }
    """
    result = {}
    raw_redis = {}
    try:
        r = _sync_redis()
        raw_redis = r.hgetall(REDIS_KEY)
    except Exception:
        pass

    for key, (conv, default) in _TYPE_MAP.items():
        if key in raw_redis:
            result[key] = {"value": _cast(key, raw_redis[key]), "source": "redis"}
        else:
            result[key] = {"value": default, "source": "env"}
    return result


def sync_runtime_to_env() -> str | None:
    """
    将 Redis 运行时配置持久化到 .env 文件。
    已有 key：就地更新值（保留原注释位置）。新 key：追加到文件末尾。
    Returns: 变更摘要字符串，无变更时返回 None
    """
    env_path = pathlib.Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if not env_path.exists():
        return ".env 文件不存在，无法同步"

    lines = env_path.read_text(encoding="utf-8").rstrip("\n").splitlines()
    env_map = {}  # VAR_NAME → line_index
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            var_name = stripped.split("=", 1)[0].strip()
            env_map[var_name] = i

    rt = get_all_runtime()
    changed = []
    new_entries = []  # 需要在末尾追加的新项

    for rt_key, (env_var, comment) in _ENV_VAR_MAP.items():
        value = rt.get(rt_key)
        if value is None:
            continue
        if isinstance(value, bool):
            new_val = str(value).lower()
        else:
            new_val = str(value)
        new_line = f"{env_var}={new_val}"

        if env_var in env_map:
            idx = env_map[env_var]
            old_line = lines[idx].strip()
            if old_line != new_line:
                # 保留原注释行（如果上一行是注释）
                if idx > 0 and lines[idx - 1].strip().startswith("#"):
                    lines[idx] = new_line  # 只改值行，保留上面注释
                else:
                    lines[idx] = f"# {comment}\n{new_line}" if "\n" not in new_line else new_line
                changed.append(f"  {env_var}: {old_line} -> {new_line}")
        else:
            new_entries.append((rt_key, env_var, comment, new_val))

    # 将新项追加到文件末尾，带区块标题和注释
    if new_entries:
        # 按区块分组
        trade_keys = ["symbol", "leverage", "timeframe", "data_points",
                      "tick_interval_seconds", "order_amount",
                      "max_position_ratio", "agent_auto_start", "agent_mode"]
        risk_keys = ["max_daily_drawdown_pct", "max_daily_loss_usdt", "sandbox"]
        trade_new = [(e, c, v) for k, e, c, v in new_entries if k in trade_keys]
        risk_new = [(e, c, v) for k, e, c, v in new_entries if k in risk_keys]

        if trade_new:
            lines.append("")
            lines.append("# ========== 交易配置（Redis 同步）==========")
            for env_var, comment, val in trade_new:
                lines.append(f"# {comment}")
                lines.append(f"{env_var}={val}")
                changed.append(f"  {env_var}: (新增) -> {env_var}={val}")
        if risk_new:
            lines.append("")
            lines.append("# ========== 风控参数（Redis 同步）==========")
            for env_var, comment, val in risk_new:
                lines.append(f"# {comment}")
                lines.append(f"{env_var}={val}")
                changed.append(f"  {env_var}: (新增) -> {env_var}={val}")

    if not changed:
        return None
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "已同步 " + str(len(changed)) + " 项配置到 .env:\n" + "\n".join(changed)


# ── 异步方法（引擎 tick 内调用）─────────────────────────

async def get_runtime_async(key: str):
    """异步读取运行时配置，Redis 优先。未命中则从 env 取值并回写 Redis。"""
    from app.database.database_redis import get_redis
    conv, default = _TYPE_MAP[key]
    try:
        r = await get_redis()
        raw = await r.hget(REDIS_KEY, key)
        if raw is not None:
            return _cast(key, raw)
        # Redis 未命中 → 用 env 默认值回写，下次直接命中
        await r.hset(REDIS_KEY, key, json.dumps(default))
    except Exception:
        pass
    return default
