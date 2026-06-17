"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: runtime_interval.py Tick 间隔热切换
描述: 检测 tick 间隔变化，动态更新调度器

包含:
- 函数: _sync_interval — 更新调度器间隔
"""

from app.services.config.runtime import get_runtime_async
from app.core.logger import get_logger

logger = get_logger()


async def _sync_interval(engine) -> None:
    """Tick 间隔变化时动态更新调度器。"""
    new_interval = int(await get_runtime_async("tick_interval_seconds"))
    if new_interval != engine.scheduler._interval:
        engine.scheduler._interval = new_interval
        logger.info(f"[运行时] Tick 间隔切换 -> {new_interval}s")
