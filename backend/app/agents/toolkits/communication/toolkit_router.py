"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_router.py 信号路由
描述: Swarm 通信路由 — 检测移交/对话信号，处理 Agent 间互问

包含:
- 函数: detect_handoff — 检测 transfer_to_X 信号
- 函数: detect_ask — 检测 ask_X 信号
- 函数: handle_asks — 处理 Agent 间对话循环
- 常量: MAX_ASK_ROUNDS / MAX_DIALOGUE_TOTAL
"""

import asyncio

from langchain_core.messages import HumanMessage, AIMessage

from app.agents.toolkits.communication.toolkit_handoff import HANDOFF_SIGNAL
from app.agents.toolkits.communication.toolkit_dialogue import ASK_SIGNAL
from app.logger import get_logger

logger = get_logger()
MAX_ASK_ROUNDS = 3
MAX_DIALOGUE_TOTAL = 10


def last_content(result: dict) -> str:
    """提取 Agent 最后一条有效输出（排除移交/对话信号消息）。"""
    msgs = result.get("messages", [])
    for m in reversed(msgs):
        c = getattr(m, "content", "") or ""
        if c and isinstance(m, AIMessage) and HANDOFF_SIGNAL not in str(c) and ASK_SIGNAL not in str(c):
            return str(c)
    return ""


def detect_handoff(result: dict) -> str | None:
    """检测 Agent 最后是否发出了 transfer_to_X 信号。"""
    for m in reversed(result.get("messages", [])):
        c = str(getattr(m, "content", ""))
        if HANDOFF_SIGNAL in c:
            target = c.split(HANDOFF_SIGNAL)[-1].split("|")[0].strip()
            logger.info(f"  ↳ 移交 → {target}")
            return target
    return None


def detect_ask(result: dict) -> tuple[str | None, str]:
    """检测 Agent 最后是否发出了 ask_X 信号，返回 (目标Agent, 问题)。"""
    for m in reversed(result.get("messages", [])):
        c = str(getattr(m, "content", ""))
        if ASK_SIGNAL in c:
            parts = c.split(ASK_SIGNAL)[-1].split("|", 1)
            target = parts[0].strip()
            question = parts[1].strip() if len(parts) > 1 else ""
            logger.info(f"  ↳ 询问 → {target}: {question[:60]}...")
            return target, question
    return None, ""


async def handle_asks(
    result: dict, asker_name: str, agents: dict, state: dict, dialogue_count: int,
) -> tuple[dict, int]:
    """处理 Agent 的 ask 请求：路由到目标 → 获取回复 → 返回给提问者。"""
    rounds = 0
    current = result

    while rounds < MAX_ASK_ROUNDS and dialogue_count < MAX_DIALOGUE_TOTAL:
        target, question = detect_ask(current)
        if not target:
            break

        target_agent = agents.get(target)
        if not target_agent:
            break

        ask_msg = [HumanMessage(content=f"[{asker_name} 提问]: {question}\n请简洁回答，不要反问。")]
        target_state = {**state, "messages": ask_msg}
        answer = await asyncio.to_thread(target_agent.invoke, target_state)
        answer_text = last_content(answer)
        logger.info(f"  ↳ {target} 回答 → {asker_name}: {answer_text[:60]}...")

        current_msgs = list(current.get("messages", []))
        current_msgs.append(HumanMessage(content=f"[{target} 回复]: {answer_text}"))
        current_state = {**state, "messages": current_msgs}
        asker_agent = agents.get(asker_name)
        if not asker_agent:
            break
        current = await asyncio.to_thread(asker_agent.invoke, current_state)

        rounds += 1
        dialogue_count += 1

    if rounds >= MAX_ASK_ROUNDS:
        logger.info(f"  ↳ {asker_name} 问询达上限({MAX_ASK_ROUNDS}轮)")
    return current, dialogue_count
