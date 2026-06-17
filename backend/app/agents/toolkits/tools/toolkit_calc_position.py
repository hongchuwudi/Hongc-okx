"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: position.py 账户持仓查询
描述: 纯计算/查询函数 — 持仓、账户、浮动盈亏。不依赖任何框架

包含:
- get_position — 当前持仓
- get_account_summary — 账户概况
- get_unrealized_pnl — 浮动盈亏
"""

from app.agents.toolkits.toolkit_data import _price, _equity, _position


def get_position() -> str:
    """获取当前持仓详情。"""
    pos = _position()
    if not pos or not pos.get("side"): return "当前持仓: 空仓"
    entry = pos.get("entry_price", 0)
    if entry <= 0: entry = _price()
    return f"持仓: {'多头' if pos['side'] == 'long' else '空头'} {pos.get('size', 0)}张 入场${entry:.2f}"


def get_account_summary() -> str:
    """获取账户概况。"""
    eq, pr, pos = _equity(), _price(), _position()
    entry = float(pos["entry_price"]) if pos and pos.get("entry_price") and float(pos["entry_price"]) > 0 else pr
    margin = float(pos["size"]) * entry * 0.01 if pos and pos.get("size") else 0.0
    pct = (margin / eq * 100) if eq > 0 else 0
    bal = eq - float(pos.get("unrealized_pnl", 0)) if pos else eq
    return f"余额${bal:,.2f} | 权益${eq:,.2f} | 保证金${margin:,.2f}({pct:.1f}%) | BTC${pr:,.2f}"


def get_unrealized_pnl() -> str:
    """获取浮动盈亏。"""
    pos, pr = _position(), _price()
    if not pos or not pos.get("side"): return "浮动盈亏: 无持仓"
    raw_entry = pos.get("entry_price")
    entry = float(raw_entry) if raw_entry is not None and float(raw_entry) > 0 else pr
    pnl, size = float(pos.get("unrealized_pnl", 0)), float(pos.get("size", 0))
    margin = entry * size * 0.01; pct = (pnl / margin * 100) if margin > 0 else 0
    return f"浮动盈亏${pnl:+.2f}({pct:+.1f}%) | 入场${entry:.2f}→当前${pr:.2f}"
