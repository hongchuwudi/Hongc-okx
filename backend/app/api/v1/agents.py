"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: agents.py Agent状态API
描述: Agent 状态查询 + 提示词热加载管理

包含:
- 端点: GET /api/agents/status — 返回 Agent 最新状态
- 端点: GET /api/agents/prompts — 获取全部提示词
- 端点: PUT /api/agents/prompts/{name} — 更新单个提示词
- 端点: POST /api/agents/prompts/{name}/reset — 重置为默认值
"""

from fastapi import APIRouter, Body, HTTPException

from app.services.agent.agent_status_service import agent_status_service
from app.schemas.responses.agent import AgentStatusResponse

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# 返回每个 Agent 的最新状态（输入/输出/移交/工具调用）+ 最近 50 条事件历史。
@router.get("/status", response_model=AgentStatusResponse)
def api_get_agents_status():
    return agent_status_service.get_status()


# === 提示词管理 ===============================================================

@router.get("/prompts")
async def api_get_prompts():
    from app.agents.prompts import get_all_prompts
    return await get_all_prompts()


@router.put("/prompts/{name}")
async def api_update_prompt(name: str, body: dict = Body(...)):
    from app.agents.prompts import set_prompt
    ok = await set_prompt(name, body.get("text", ""))
    if not ok:
        raise HTTPException(400, f"未知的 Agent: {name}")
    return {"ok": True, "message": f"{name} 提示词已更新"}


@router.post("/prompts/{name}/reset")
async def api_reset_prompt(name: str):
    from app.agents.prompts import reset_prompt
    ok = await reset_prompt(name)
    if not ok:
        raise HTTPException(400, f"未知的 Agent: {name}")
    return {"ok": True, "message": f"{name} 提示词已重置"}


@router.post("/reload")
async def api_reload_agents():
    from app.services.engine.engine_control import force_reload_agents
    ok = await force_reload_agents()
    return {"ok": ok, "message": "Agent 已热重载" if ok else "引擎未运行，变更将在下一 tick 生效"}


@router.get("/decisions")
def api_get_decisions(page: int = 1, page_size: int = 20):
    from app.agents.status import query_agent_decisions
    return query_agent_decisions(page, page_size)
