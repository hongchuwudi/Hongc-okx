"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_memory_private.py 私有记忆工具（PG持久化版）
描述: 每个 Agent 独立的持久化私有记忆 — ORM 写入 PostgreSQL，重启不丢失

包含:
- 函数: create_memory_tools — 传入 agent_name，返回 [remember, recall, check_my_accuracy]
"""

import threading
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.entities.agent_private_memory import AgentPrivateMemory

_lock = threading.Lock()
_pg_available = True
_max_entries = 20
_fallback_stores: dict[str, dict] = {}


def _save(agent_name: str, key: str, value: str) -> None:
    """UPSERT 写入（ORM）。PG 不可用时降级到内存。"""
    global _pg_available
    if not _pg_available:
        s = _fallback_stores.setdefault(agent_name, {})
        if len(s) >= _max_entries:
            oldest = next(iter(s))
            del s[oldest]
        s[key] = value
        return

    session: Session = get_sync_session()
    try:
        row = session.get(AgentPrivateMemory, (agent_name, key))
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            session.add(AgentPrivateMemory(
                agent_name=agent_name, key=key, value=value,
                updated_at=datetime.utcnow(),
            ))
        session.commit()
    except Exception:
        _pg_available = False
        _save(agent_name, key, value)
    finally:
        session.close()


def _load_all(agent_name: str) -> dict:
    """加载指定 Agent 的所有记忆。PG 不可用时从内存读。"""
    if not _pg_available:
        return dict(_fallback_stores.get(agent_name, {}))

    session: Session = get_sync_session()
    try:
        rows = (
            session.query(AgentPrivateMemory)
            .filter(AgentPrivateMemory.agent_name == agent_name)
            .order_by(AgentPrivateMemory.updated_at.desc())
            .limit(20)
            .all()
        )
        return {r.key: r.value for r in rows}
    except Exception:
        return {}
    finally:
        session.close()


def create_memory_tools(agent_name: str) -> list:
    """为指定 Agent 创建 remember + recall + check_my_accuracy 工具。"""

    @tool
    def remember(key: str, value: str) -> str:
        """记住一条经验。key=要记的事, value=详细内容。写入 PG 持久化。"""
        with _lock:
            _save(agent_name, key, value)
        return f"[{agent_name}] 已记住: {key}"

    @tool
    def recall(key: str = "") -> str:
        """回忆过去的经验。key=查什么，留空返回所有记忆摘要。"""
        store = _load_all(agent_name)
        if not store:
            return f"[{agent_name}] 暂无记忆"
        if key and key in store:
            return f"[{agent_name}] {key}: {store[key]}"
        if key:
            return f"[{agent_name}] 不记得 {key}"
        lines = [f"[{agent_name}] 记忆共 {len(store)} 条:"]
        for k, v in store.items():
            lines.append(f"  {k}: {str(v)[:100]}")
        return "\n".join(lines)

    @tool
    def check_my_accuracy() -> str:
        """检查我自己的历史判断准确率。统计私有记忆中记录了多少次预测、对了多少次。"""
        store = _load_all(agent_name)
        total = 0
        correct = 0
        for k, v in store.items():
            if k.startswith("result_"):
                total += 1
                if "对了" in str(v):
                    correct += 1
        if total == 0:
            return f"[{agent_name}] 暂无历史预测记录，首次运行"
        rate = correct / total * 100
        return f"[{agent_name}] 历史准确率: {correct}/{total} ({rate:.0f}%) — 共 {total} 次预测"

    remember.name = "remember"
    remember.description = f"记住一条经验到 {agent_name} 的私有记忆。做预测前记住 prediction_xxx，看到反馈后记住 result_xxx=对了/错了。"
    recall.name = "recall"
    recall.description = f"回忆 {agent_name} 的私有记忆。"
    check_my_accuracy.name = "check_my_accuracy"
    check_my_accuracy.description = f"查看 {agent_name} 自己的历史预测准确率。"

    return [remember, recall, check_my_accuracy]
