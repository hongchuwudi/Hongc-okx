"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: memory.py 交易记忆查询
描述: 纯查询函数 — 历史统计、最近交易、经验教训。不依赖任何框架

包含:
- get_trade_stats — 交易统计
- get_recent_trades — 最近交易记录
- get_lessons — 经验教训
"""


def _store():
    from app.memory import memory_store
    return memory_store


def get_trade_stats() -> str:
    """获取历史交易统计。"""
    s = _store().get_stats()
    return f"总决策{s['total']} | 胜率{s['win_rate']}% | 均盈亏{s['avg_pnl']:.4f} | {s['recent_trend']}"


def get_recent_trades(limit: int = 10) -> str:
    """获取最近 N 笔交易记录。"""
    recent = _store().get_recent(limit)
    if not recent: return "暂无历史交易"
    lines = [f"最近{len(recent)}笔:"]
    for m in recent:
        pnl = m.get("outcome_pnl") or 0
        lines.append(f"  {m.get('timestamp', '')} {m.get('signal', ''):4s} @${m.get('price', 0):,.0f} → {pnl:+.2f}")
    return "\n".join(lines)


def get_lessons() -> str:
    """从历史交易中提取经验教训。"""
    s = _store().get_stats(); recent = _store().get_recent(10)
    lines = ["【历史经验】"]
    trend = s.get("recent_trend", "")
    if "连续盈利" in trend: lines.append(f"✓ {trend}—可适度增加信心")
    elif "连续亏损" in trend: lines.append(f"⚠ {trend}—建议降低仓位或暂停")
    wins = sum(1 for r in recent if r.get("is_win"))
    losses = sum(1 for r in recent if r.get("is_win") is False)
    if recent: lines.append(f"近{len(recent)}笔:{wins}赢{losses}亏")
    if losses >= 3 and wins == 0: lines.append("建议:连续亏损→暂停或缩仓50%")
    elif wins >= 3 and losses == 0: lines.append("建议:连续盈利→保持策略,防过度自信")
    return "\n".join(lines)
