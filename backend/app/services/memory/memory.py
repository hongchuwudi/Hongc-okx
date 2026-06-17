"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: memory_service.py 记忆服务
描述: AI 交易记忆管理 — 记录决策、更新结果、查询历史、生成摘要

包含:
- 类: MemoryService — AI 交易记忆管理服务
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.entities.memory import TradeMemory


# AI 交易记忆服务 — 记录决策、更新结果、生成统计
class MemoryService:

    # 记录一次 AI 决策，返回记忆 ID
    def add(self, signal: str, confidence: str, reason: str,
            price: float, market_state: str = "") -> int:
        s: Session = get_sync_session()
        try:
            m = TradeMemory(
                timestamp=datetime.utcnow(), signal=signal,
                confidence=confidence, reason=reason, price=price,
                market_state=market_state,
            )
            s.add(m)
            s.commit()
            return m.id
        finally:
            s.close()

    # 记录某次决策的最终交易结果（平仓后调用）
    def update_outcome(self, memory_id: int, pnl: float) -> None:
        s: Session = get_sync_session()
        try:
            m = s.query(TradeMemory).filter_by(id=memory_id).first()
            if m:
                m.outcome_pnl = round(pnl, 4)
                m.is_win = pnl > 0
                m.closed_at = datetime.utcnow()
                s.commit()
        finally:
            s.close()

    # 取最近 N 条记忆记录
    def get_recent(self, limit: int = 10) -> list[dict]:
        s: Session = get_sync_session()
        try:
            rows = (
                s.query(TradeMemory)
                .order_by(TradeMemory.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.strftime("%m-%d %H:%M") if r.timestamp else "",
                    "signal": r.signal, "confidence": r.confidence,
                    "reason": (r.reason or "")[:60],
                    "price": r.price, "market_state": r.market_state or "",
                    "outcome_pnl": r.outcome_pnl, "is_win": r.is_win,
                }
                for r in rows
            ]
        finally:
            s.close()

    # 生成记忆统计摘要（胜率、平均盈亏、近期趋势等）
    def get_stats(self) -> dict:
        s: Session = get_sync_session()
        try:
            total = s.query(TradeMemory).count()
            if total == 0:
                return {"total": 0, "win_rate": 0, "avg_pnl": 0, "recent_trend": "无记录"}

            closed = s.query(TradeMemory).filter(TradeMemory.outcome_pnl.isnot(None)).all()
            wins = [t for t in closed if t.is_win]
            losses = [t for t in closed if t.is_win is False]
            win_rate = len(wins) / len(closed) * 100 if closed else 0
            avg_pnl = sum(t.outcome_pnl for t in closed) / len(closed) if closed else 0

            recent = closed[-5:] if len(closed) >= 5 else closed
            recent_wins = sum(1 for t in recent if t.is_win)
            if recent_wins >= 4:
                trend = "近况优秀"
            elif recent_wins >= 3:
                trend = "近况良好"
            elif recent_wins >= 2:
                trend = "近况一般"
            else:
                trend = "近况较差，需谨慎"

            return {
                "total": total, "closed": len(closed),
                "wins": len(wins), "losses": len(losses),
                "win_rate": round(win_rate, 1),
                "avg_pnl": round(avg_pnl, 4),
                "recent_trend": trend,
            }
        finally:
            s.close()

    # 生成可插入 LLM prompt 的记忆文本，含近期决策和统计
    def build_prompt_context(self, limit: int = 10) -> str:
        recent = self.get_recent(limit)
        stats = self.get_stats()

        if not recent:
            return "【交易记忆】暂无历史记录，这是首次决策。"

        lines = [f"【交易记忆 — 近期 {len(recent)} 次决策】"]
        for m in reversed(recent):
            outcome = ""
            if m["outcome_pnl"] is not None:
                sign = "+" if (m["outcome_pnl"] or 0) >= 0 else ""
                outcome = f" 结果: {sign}{m['outcome_pnl']:.2f} USDT {'✓' if m['is_win'] else '✗'}"

            lines.append(
                f"{m['timestamp']} | {m['signal']:4s} {m['confidence']:6s} | "
                f"理由: {m['reason']}{outcome}"
            )

        lines.append("")
        lines.append(
            f"【绩效摘要】总决策: {stats['total']} | 已结算: {stats.get('closed', 0)} | "
            f"胜率: {stats['win_rate']}% | 平均盈亏: {stats['avg_pnl']:.4f} USDT | "
            f"{stats['recent_trend']}"
        )
        lines.append("请参考历史表现，避免重复犯过的错误。")

        return "\n".join(lines)


# 全局单例
memory_service = MemoryService()
