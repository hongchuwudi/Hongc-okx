"""
创建时间: 2026-06-23
作者: hongchuwudi
文件名: agent_balance_service.py DeepSeek 余额查询服务
描述: 查询 DeepSeek 账户余额 — GET /user/balance，供 API 端点与 engine 降级使用

DeepSeek 余额接口（OpenAI 兼容平台，独立于 chat completions）:
- 端点: GET {base_url}/user/balance
- 鉴权: Authorization: Bearer {api_key}
- 返回: { is_available: bool, balance_infos: [{currency, total_balance, ...}] }
- total_balance 为字符串（CNY），如 "10.50" 或欠费 "-0.10"

包含:
- 函数: _query_balance_sync — 同步调用 DeepSeek 余额接口（核心实现）
- 函数: get_deepseek_balance — 同步查询，返回余额 dict（API 端点用）
- 函数: get_deepseek_balance_async — 异步查询（engine tick 内用）
- 函数: check_balance_sufficient — 余额是否充足，供 engine 降级判断
- 常量: BALANCE_DEGRADE_THRESHOLD — 触发降级的技术指标方案阈值（CNY）
"""
import asyncio

import httpx

from app.core.config import config
from app.core.exceptions import ExternalServiceError
from app.core.logger import get_logger

logger = get_logger()

# 余额低于此值（CNY）时，engine 自动降级为技术指标方案，不走 agent 路线
BALANCE_DEGRADE_THRESHOLD = 0.05

# 余额接口路径（拼接在 base_url 之后）
_BALANCE_PATH = "/user/balance"

# 复用无代理 httpx client（与 model_scheduler.py 一致，国内环境走系统代理）
_client = httpx.Client(proxy=None, timeout=10.0)


# ── 同步核心实现 ────────────────────────────────────────────

def _query_balance_sync() -> dict:
    """同步调用 DeepSeek 余额接口，返回原始 JSON dict。

    Raises:
        ExternalServiceError: 接口不可达或返回非 200。
    """
    url = config.ai.deepseek_base_url.rstrip("/") + _BALANCE_PATH
    headers = {"Authorization": f"Bearer {config.ai.deepseek_api_key}"}
    try:
        resp = _client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise ExternalServiceError(
            f"DeepSeek 余额查询失败: {type(e).__name__}: {e}",
            detail={"url": url},
        )


# ── 对外查询接口 ────────────────────────────────────────────

def get_deepseek_balance() -> dict:
    """同步查询 DeepSeek 余额，返回标准化 dict。

    Returns:
        {
            is_available: bool,        # 账户是否可用
            total_balance: float,      # 总余额（CNY，float）
            currency: str,             # 币种，通常 "CNY"
            granted_balance: float,    # 赠送余额
            topped_up_balance: float,  # 充值余额
            raw: dict,                 # 原始接口返回
        }
    """
    raw = _query_balance_sync()
    infos = raw.get("balance_infos") or []
    info = infos[0] if infos else {}
    return {
        "is_available": bool(raw.get("is_available")),
        "total_balance": float(info.get("total_balance", 0) or 0),
        "currency": info.get("currency", "CNY"),
        "granted_balance": float(info.get("granted_balance", 0) or 0),
        "topped_up_balance": float(info.get("topped_up_balance", 0) or 0),
        "raw": raw,
    }


async def get_deepseek_balance_async() -> dict:
    """异步查询 DeepSeek 余额（engine tick 内调用）。

    用 asyncio.to_thread 包装同步实现，避免阻塞事件循环。
    """
    return await asyncio.to_thread(get_deepseek_balance)


# ── engine 降级判断 ─────────────────────────────────────────

async def check_balance_sufficient(
    threshold: float = BALANCE_DEGRADE_THRESHOLD,
) -> tuple[bool, float]:
    """余额是否充足，供 engine 降级判断。

    Returns:
        (sufficient, balance) — sufficient=True 表示余额 >= threshold，可走 agent；
        sufficient=False 表示余额不足，应降级为技术指标。

    余额查询失败时返回 (True, -1) — 容错不阻断 agent 路线，
    让原有 AI 调用失败降级逻辑兜底（避免余额接口故障误降级）。
    """
    try:
        info = await get_deepseek_balance_async()
        balance = info["total_balance"]
        sufficient = balance >= threshold
        if not sufficient:
            logger.warning(
                f"DeepSeek 余额不足: {balance} < {threshold}，将降级为技术指标方案"
            )
        return sufficient, balance
    except Exception as e:
        # 余额接口故障时不阻断 agent，让 AI 调用自身的失败降级兜底
        logger.warning(f"余额查询失败(不阻断 agent): {type(e).__name__}: {e}")
        return True, -1.0
