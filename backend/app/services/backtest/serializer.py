"""
创建时间: 2026-06-14
作者: hongchuwudi
描述: 回测序列化 — ORM 对象转 dict，供 API 和 Service 层使用

包含:
- 函数: run_summary — BacktestRun → 列表摘要 dict
- 函数: run_detail — BacktestRun → 完整详情 dict
"""

import json

from app.entities.backtest import BacktestRun


# 回测运行摘要 — 提取列表页所需的核心字段
def run_summary(r: BacktestRun) -> dict:
    return {
        # 运行 ID
        "id": r.id,
        # 策略名称
        "strategy_name": r.strategy_name,
        # 交易品种
        "symbol": r.symbol,
        # 时间周期
        "timeframe": r.timeframe,
        # 数据条数
        "data_count": r.data_count,
        # 运行状态: running / completed / failed
        "status": r.status,
        # 总收益率（%）
        "total_return_pct": r.total_return_pct,
        # 胜率（%）
        "win_rate": r.win_rate,
        # 盈亏比
        "profit_factor": r.profit_factor,
        # 最大回撤（%）
        "max_drawdown_pct": r.max_drawdown_pct,
        # 夏普比率
        "sharpe_ratio": r.sharpe_ratio,
        # 总交易次数
        "total_trades": r.total_trades,
        # 开始时间 (ISO 格式)
        "started_at": r.started_at.isoformat() if r.started_at else None,
        # 完成时间 (ISO 格式)
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }


# 回测运行详情 — 提取单条记录的完整信息，含交易列表和权益曲线
def run_detail(r: BacktestRun) -> dict:
    return {
        # 请求是否成功
        "ok": True,
        # 运行 ID
        "id": r.id,
        # 策略名称
        "strategy_name": r.strategy_name,
        # 交易品种
        "symbol": r.symbol,
        # 时间周期
        "timeframe": r.timeframe,
        # 数据条数
        "data_count": r.data_count,
        # 预热期
        "warmup": r.warmup,
        # 运行状态
        "status": r.status,
        # 初始资金
        "initial_capital": r.initial_capital,
        # 最终权益
        "final_equity": r.final_equity,
        # 总收益率（%）
        "total_return_pct": r.total_return_pct,
        # 胜率（%）
        "win_rate": r.win_rate,
        # 盈亏比
        "profit_factor": r.profit_factor,
        # 最大回撤（%）
        "max_drawdown_pct": r.max_drawdown_pct,
        # 夏普比率
        "sharpe_ratio": r.sharpe_ratio,
        # 总交易次数
        "total_trades": r.total_trades,
        # 盈利次数
        "winning_trades": r.winning_trades,
        # 亏损次数
        "losing_trades": r.losing_trades,
        # 平均交易盈亏
        "avg_trade_pnl": r.avg_trade_pnl,
        # 开始时间 (ISO 格式)
        "started_at": r.started_at.isoformat() if r.started_at else None,
        # 完成时间 (ISO 格式)
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        # 错误信息
        "error_message": r.error_message,
        # 交易记录列表（从 JSON 解析）
        "trades": json.loads(r.trades_json) if r.trades_json else [],
        # 权益曲线数据（从 JSON 解析）
        "equity_curve": json.loads(r.equity_json) if r.equity_json else [],
    }