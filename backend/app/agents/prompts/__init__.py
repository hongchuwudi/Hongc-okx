"""
创建时间: 2026-06-16
作者: hongchuwudi
文件名: __init__.py 提示词模块导出 + 热加载
描述: 7 个 Agent 提示词汇总导出，支持 Redis 热加载（Redis 优先，文件兜底）

包含:
- 常量: PROMPT_DEFAULTS — 提示词名称 → (文件默认值, 中文标签) 映射
- 函数: get_prompt(name) — 异步获取提示词（Redis 优先）
- 函数: set_prompt(name, text) — 异步更新提示词到 Redis
- 函数: reset_prompt(name) — 重置为文件默认值
- 函数: get_all_prompts() — 获取全部提示词状态
- 函数: get_prompt_version() — 获取当前提示词版本号
"""

import asyncio

from app.agents.prompts.prompt_scheduler import SCHEDULER_PROMPT
from app.agents.prompts.prompt_analyst import ANALYST_PROMPT
from app.agents.prompts.prompt_reviewer import REVIEWER_PROMPT
from app.agents.prompts.prompt_risk import RISK_PROMPT
from app.agents.prompts.prompt_trader import TRADER_PROMPT
from app.agents.prompts.prompt_super_analyst import SUPER_ANALYST_PROMPT
from app.agents.prompts.prompt_solo import SOLO_PROMPT

# 提示词名称 → (文件默认值, 中文标签)
PROMPT_DEFAULTS: dict[str, tuple[str, str]] = {
    "scheduler":      (SCHEDULER_PROMPT,       "调度师"),
    "analyst":        (ANALYST_PROMPT,         "分析师"),
    "reviewer":       (REVIEWER_PROMPT,        "复盘师"),
    "risk":           (RISK_PROMPT,            "风控师"),
    "trader":         (TRADER_PROMPT,          "交易员"),
    "super_analyst":  (SUPER_ANALYST_PROMPT,   "超级分析师"),
    "solo":           (SOLO_PROMPT,            "Solo"),
}

_REDIS_KEY_PREFIX = "agent:prompt"
_VERSION_KEY = f"{_REDIS_KEY_PREFIX}:version"
_H = ("\n你拥有 check_my_accuracy 工具查看自己的历史准确率。"
      "\n每次做预测时先 remember('prediction','你的预测内容')，看到反馈后 remember('result_xxx','对了/错了+原因')。")


def _redis_key(name: str) -> str:
    return f"{_REDIS_KEY_PREFIX}:{name}"


async def get_prompt(name: str) -> str:
    """获取完整提示词，Redis 优先，文件兜底（自动追加通用后缀）。"""
    try:
        from app.database import get_redis
        redis = await get_redis()
        text = await redis.get(_redis_key(name))
        if text:
            return text
    except Exception:
        pass
    default, _ = PROMPT_DEFAULTS.get(name, ("", ""))
    return default + _H


def get_prompt_sync(name: str) -> str:
    """同步版获取完整提示词，通过同步 Redis 客户端，用于构建 Agent。"""
    try:
        from app.database.database_redis import get_redis_sync
        text = get_redis_sync().get(_redis_key(name))
        if text:
            return text
    except Exception:
        pass
    default, _ = PROMPT_DEFAULTS.get(name, ("", ""))
    return default + _H


async def set_prompt(name: str, text: str) -> bool:
    """更新提示词到 Redis 并增加版本号。"""
    if name not in PROMPT_DEFAULTS:
        return False
    try:
        from app.database import get_redis
        redis = await get_redis()
        await redis.set(_redis_key(name), text)
        await redis.incr(_VERSION_KEY)
        return True
    except Exception:
        return False


async def reset_prompt(name: str) -> bool:
    """重置单个提示词为文件默认值。"""
    if name not in PROMPT_DEFAULTS:
        return False
    try:
        from app.database import get_redis
        redis = await get_redis()
        await redis.delete(_redis_key(name))
        await redis.incr(_VERSION_KEY)
        return True
    except Exception:
        return False


async def get_all_prompts() -> list[dict]:
    """获取全部提示词状态（名称、标签、当前值、是否已修改）。"""
    result = []
    for name, (default, label) in PROMPT_DEFAULTS.items():
        current = default + _H
        modified = False
        try:
            from app.database import get_redis
            redis = await get_redis()
            text = await redis.get(_redis_key(name))
            if text:
                current = text
                modified = True
        except Exception:
            pass
        result.append({
            "name": name,
            "label": label,
            "text": current,
            "default": default + _H,
            "modified": modified,
        })
    return result


async def get_prompt_version() -> int:
    """获取当前提示词版本号。"""
    try:
        from app.database import get_redis
        redis = await get_redis()
        v = await redis.get(_VERSION_KEY)
        return int(v) if v else 0
    except Exception:
        return 0
