"""
创建时间: 2026-06-07
作者: hongchuwudi
文件名: toolkit_calc_feedback.py 学习闭环
描述: 每 tick 检查上一轮决策结果，生成反馈信息供所有 Agent 学习

包含:
- 函数: generate_feedback — 对比上次决策 vs 实际结果，返回反思文本
"""

from app.agents.toolkits.toolkit_data import _price, _position


def generate_feedback() -> str:
    """对比上一轮决策和实际结果，生成反馈文本。"""
    pos = _position()
    price = _price()

    lines = []

    # 有持仓 → 上一次决策执行了
    if pos and pos.get("side") and pos.get("entry_price") is not None:
        pnl = float(pos.get("unrealized_pnl", 0))
        entry = float(pos.get("entry_price", price))
        if entry <= 0:
            entry = price
        size = float(pos.get("size", 0))
        direction = "多头" if pos["side"] == "long" else "空头"
        margin = entry * size * 0.01
        pnl_pct = (pnl / margin * 100) if margin > 0 else 0

        if pnl > 0:
            verdict = "对了"
            lines.append(f"【上一轮反馈】{direction}入场 @ ${entry:.0f}，浮动盈亏 ${pnl:+.2f} ({pnl_pct:+.1f}%) — {verdict}")
            lines.append("上一轮决策方向正确，当前策略可以参考。")
        else:
            verdict = "错了"
            lines.append(f"【上一轮反馈】{direction}入场 @ ${entry:.0f}，浮动盈亏 ${pnl:+.2f} ({pnl_pct:+.1f}%) — {verdict}")
            lines.append("上一轮决策方向有误，请各 Agent 反思：是技术指标误判还是市场环境突变？")
    else:
        lines.append("【上一轮反馈】上一轮未开仓（HOLD），无持仓反馈")

    return "\n".join(lines)
