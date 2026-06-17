"""
创建时间: 2026-06-14
作者: hongchuwudi
描述: 回测执行器辅助函数 — 策略工厂 + DB 记录管理 + 结果持久化，消除 run/run_stream 之间的重复代码

包含:
- 函数: _ensure_run — 创建或合并 BacktestRun 数据库记录
- 函数: _build_strategy — 策略实例工厂
- 函数: _save_run_result — 将回测结果写入 BacktestRun 并提交数据库
- 函数: _config_json — 生成回测配置 JSON 字符串
"""

import json
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.entities.backtest import BacktestRun
from app.core.exceptions import BusinessError


# 确保回测运行记录存在 — 有 pre_run 则合并，否则创建新记录并返回 (记录, run_id)
def _ensure_run(
    session: Session,
    strategy: str, symbol: str, timeframe: str,
    initial_capital: float, position_ratio: float, fee_rate: float,
    data_limit: int, warmup: int,
    pre_run: BacktestRun | None = None,
) -> Tuple[BacktestRun, int]:
    # 如果传入了已有的运行记录，合并到当前会话
    if pre_run:
        run = session.merge(pre_run)
        return run, run.id

    # 新建回测运行记录，状态设为 running
    run = BacktestRun(
        strategy_name=strategy, symbol=symbol, timeframe=timeframe,
        initial_capital=initial_capital, position_ratio=position_ratio,
        fee_rate=fee_rate, data_count=data_limit, warmup=warmup,
        status="running", started_at=datetime.utcnow(),
    )
    session.add(run)
    session.commit()
    return run, run.id


# 策略实例工厂 — 根据策略类型创建策略对象，返回 (策略实例, 调整后的 data_limit)
def _build_strategy(strategy: str, symbol: str, timeframe: str, data_limit: int, temperature: float = 0.1):
    if strategy == "technical":
        from app.services.strategies.strategy_technical import TechnicalStrategy
        return TechnicalStrategy(), data_limit

    raise BusinessError(f"未知策略: {strategy}")


# 回测结果持久化 — 将性能指标、交易记录、权益曲线写入数据库
def _save_run_result(
    run: BacktestRun,
    metrics: dict,
    trades_json: str,
    equity_json: str,
    config_json: str,
    session: Session,
):
    # 状态标记为完成
    run.status = "completed"
    # 写入各项性能指标
    run.final_equity = metrics["final_equity"]
    run.total_return_pct = metrics["total_return_pct"]
    run.win_rate = metrics["win_rate"]
    run.profit_factor = metrics["profit_factor"]
    run.max_drawdown_pct = metrics["max_drawdown_pct"]
    run.sharpe_ratio = metrics["sharpe_ratio"]
    run.total_trades = metrics["total_trades"]
    run.winning_trades = metrics["winning_trades"]
    run.losing_trades = metrics["losing_trades"]
    run.avg_trade_pnl = metrics["avg_trade_pnl"]
    # 记录完成时间
    run.finished_at = datetime.utcnow()
    # 写入 JSON 字段
    run.metrics_json = json.dumps(metrics, ensure_ascii=False)
    run.config_json = config_json
    run.trades_json = trades_json
    run.equity_json = equity_json
    session.commit()


# 生成回测配置 JSON — 将参数序列化为配置字符串供前端展示
def _config_json(strategy: str, symbol: str, timeframe: str,
                 initial_capital: float, position_ratio: float, fee_rate: float,
                 warmup: int, data_limit: int) -> str:
    return json.dumps({
        "strategy": strategy, "symbol": symbol, "timeframe": timeframe,
        "initial_capital": initial_capital, "position_ratio": position_ratio,
        "fee_rate": fee_rate, "warmup": warmup, "data_limit": data_limit,
    }, ensure_ascii=False)