"""
创建时间: 2026-06-22
作者: hongchuwudi
文件名: runtime_prompt.py 提示词热重载
描述: 检测提示词版本变化，自动重建 coordinator

包含:
- 函数: _sync_prompt — 提示词变化时重建 coordinator
"""

from app.core.logger import get_logger

logger = get_logger()


async def _sync_prompt(engine) -> None:
    """Redis 提示词版本变化时重建 coordinator。"""
    if not engine.use_multi_agent or engine.coordinator is None:
        return

    try:
        from app.agents.prompts import get_prompt_version
        pv = await get_prompt_version()
        if pv != engine._last_prompt_version:
            engine._last_prompt_version = pv
            logger.info("[运行时] 检测到提示词变更，重建 Agent...")
            # 根据当前模式重建对应 coordinator
            from app.services.agent.agent_coordinator_service import (
                create_coordinator, create_coordinator_3, create_coordinator_solo,
            )
            mode = engine._last_mode
            if mode == "1_agent":
                engine.coordinator = create_coordinator_solo()
            elif mode == "3_agent":
                engine.coordinator = create_coordinator_3()
            else:
                engine.coordinator = create_coordinator()
            logger.info("[运行时] Agent 已热重载")
    except Exception:
        pass
