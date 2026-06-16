"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: tick_circuit.py 熔断检查
描述: 每个 tick 的熔断状态检查 — 暂停冷却 / 已停止则跳过本 tick

包含:
- 函数: tick_check_circuit — 检查熔断状态，True 继续 / False 跳过
"""

from app.engine.loop.tick_persistence import publish_event
from app.core.logger import get_logger

logger = get_logger()


async def tick_check_circuit(engine) -> bool:
    """检查熔断状态。返回 True 表示可以继续，False 表示跳过本轮 tick。

    暂停中：推送 paused 事件 + 返回 False
    已停止：记录日志 + 返回 False
    正常：返回 True
    """
    # 暂停冷却检查
    pause_info = await engine.risk.check_pause()
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
        return False

    # 已停止检查
    cb_state = await engine.risk.get_circuit_state()
    if cb_state["stopped"]:
        logger.warning("熔断已停止引擎，跳过本轮 tick (请通过 API 或前端重置)")
        return False

    return True
