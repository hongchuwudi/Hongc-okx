"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: risk.py 风控计算
描述: 纯计算函数 — 风险评估、仓位上限、止损止盈。不依赖任何框架

包含:
- evaluate_position_risk — 持仓风险评估
- calc_max_position — 仓位上限
- calc_sl_tp — 止损止盈
"""

from app.agents.toolkits.toolkit_data import _price, _equity, _position


def evaluate_position_risk() -> str:
    """评估当前持仓风险等级。"""
    pos, pr, eq = _position(), _price(), _equity()
    if not pos or not pos.get("side"): return "风险: 无持仓"
    pnl = float(pos.get("unrealized_pnl", 0)); entry = float(pos.get("entry_price", pr)); size = float(pos.get("size", 0))
    margin = entry * size * 0.01; ratio = pnl / margin if margin > 0 else 0; mpct = (margin / eq * 100) if eq > 0 else 0
    risks = []
    if ratio < -0.5: risks.append("浮亏超保证金50%")
    if mpct > 30: risks.append("保证金占比过高")
    if ratio > 1.0: risks.append("大幅盈利中")
    lv = "高" if (ratio < -0.3 or mpct > 30) else ("低" if ratio > 0.3 else "正常")
    return f"风险:{lv} | 保证金占比{mpct:.1f}% | 浮亏/保证金{ratio:+.1%}" + (f" | {';'.join(risks)}" if risks else "")


def calc_max_position(confidence: str, atr_pct: float) -> str:
    """根据置信度和波动率计算最大仓位。"""
    cf = {"HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}
    base = cf.get(confidence.upper(), 0.3)
    atr = max(float(atr_pct), 0.5); vd = max(0.3, 1.0 - (atr - 1.0) * 0.2)
    maxp = min(base * vd * 50, 50)
    return f"最大仓位{maxp:.0f}% (置信度{confidence}→{base:.1f} × 波动率{atr:.1f}%→{vd:.0%})"


def calc_sl_tp(direction: str, atr_pct: float) -> str:
    """根据方向和波动率计算止损止盈（短线参数）。"""
    pr, atr = _price(), float(atr_pct)
    sl_pct = min(max(atr * 0.8, 0.3), 3.0)   # 短线：止损 0.3%~3%
    tp_pct = min(max(atr * 1.5, 0.6), 5.0)   # 短线：止盈 0.6%~5%
    if direction.lower() == "long": sl, tp = pr * (1 - sl_pct / 100), pr * (1 + tp_pct / 100)
    else: sl, tp = pr * (1 + sl_pct / 100), pr * (1 - tp_pct / 100)
    return f"方向{direction.upper()} | 止损${sl:.0f}({sl_pct:.1f}%) | 止盈${tp:.0f}({tp_pct:.1f}%) | 盈亏比1:{tp_pct / sl_pct:.1f}"
