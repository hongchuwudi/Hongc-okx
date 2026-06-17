"""
创建时间: 2026-06-14
作者: hongchuwudi
描述: 引擎运行状态控制 — 全局变量 + 启停逻辑，供 API 和 run.py 共享
"""

import asyncio
from app.core.logger import get_logger

logger = get_logger()

_running = False
_scheduler = None
_engine_task: asyncio.Task | None = None
_engine = None  # 持有引擎引用，供 API 触发即时同步


def set_running(scheduler):
    global _running, _scheduler
    _running = True
    _scheduler = scheduler


def get_status() -> dict:
    return {"running": _running}


async def start():
    global _running, _scheduler, _engine_task, _engine
    if _running:
        logger.warning("引擎已在运行中，跳过重复启动")
        return

    from app.engine import TradingEngine
    _engine = TradingEngine()
    set_running(_engine.scheduler)

    _engine_task = asyncio.create_task(_run_engine(_engine))
    logger.info("引擎已启动 (通过 API 触发)")


async def _run_engine(engine):
    global _running, _scheduler, _engine_task, _engine
    try:
        await engine.run()
    except Exception as e:
        logger.error(f"引擎异常退出: {e}")
    finally:
        _running = False
        _scheduler = None
        _engine_task = None
        _engine = None
        logger.info("引擎已退出")


async def force_reload_agents() -> bool:
    """强制引擎即时重建 Agent（提示词变更后调用）。"""
    global _engine
    if _engine is None:
        return False
    try:
        await _engine._sync_runtime()
        return True
    except Exception as e:
        logger.error(f"强制重载 Agent 失败: {e}")
        return False


async def stop():
    global _running, _scheduler, _engine_task
    if _scheduler:
        await _scheduler.stop()
    if _engine_task and not _engine_task.done():
        _engine_task.cancel()
        try:
            await _engine_task
        except asyncio.CancelledError:
            pass
    _running = False
    _scheduler = None
    _engine_task = None
    logger.info("引擎已停止")
