
"""回测 API — /api/backtest/*"""

import asyncio
import json
import traceback
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_sync_session
from app.models.backtest import BacktestRun

router = APIRouter(prefix="/api/backtest")


class RunRequest(BaseModel):
    strategy: str = "technical"
    symbol: str = "BTC/USDT:USDT"
    timeframe: str = "1h"
    initial_capital: float = 100.0
    position_ratio: float = 0.5
    fee_rate: float = 0.001
    warmup: int = 50
    data_limit: int = 500


@router.post("/run")
def start_backtest(req: RunRequest):
    """触发一次回测（同步执行，返回结果）"""
    session: Session = get_sync_session()
    run: Optional[BacktestRun] = None
    try:
        # 创建记录
        run = BacktestRun(
            strategy_name=req.strategy,
            symbol=req.symbol,
            timeframe=req.timeframe,
            initial_capital=req.initial_capital,
            position_ratio=req.position_ratio,
            fee_rate=req.fee_rate,
            data_count=req.data_limit,
            warmup=req.warmup,
            status="running",
            started_at=datetime.utcnow(),
        )
        session.add(run)
        session.commit()
        run_id = run.id

        # 下载数据
        import ccxt
        from app.config import config

        exchange = ccxt.okx({"hostname": "www.okx.cab", "enableRateLimit": True, "verify": False})
        if config.okx.proxy:
            exchange.https_proxy = config.okx.proxy
        ohlcv = exchange.fetch_ohlcv(req.symbol, req.timeframe, limit=req.data_limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # 初始化策略
        if req.strategy == "technical":
            from app.strategies.technical import TechnicalStrategy
            strategy = TechnicalStrategy()
        elif req.strategy == "deepseek":
            from app.strategies.deepseek import DeepSeekStrategy
            from openai import OpenAI
            from app.config import config
            client = OpenAI(api_key=config.ai.deepseek_api_key, base_url=config.ai.deepseek_base_url)
            strategy = DeepSeekStrategy({
                "symbol": req.symbol, "timeframe": req.timeframe, "leverage": 1,
            }, client)
        else:
            run.status = "failed"
            run.error_message = f"未知策略: {req.strategy}"
            session.commit()
            return {"ok": False, "error": run.error_message}

        # 运行回测
        from app.backtest.engine import run_backtest
        result = run_backtest(
            df, strategy,
            initial_capital=req.initial_capital,
            position_ratio=req.position_ratio,
            fee_rate=req.fee_rate,
            warmup=req.warmup,
        )
        metrics = result["metrics"]

        # 更新结果
        run.status = "completed"
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
        run.finished_at = datetime.utcnow()
        run.metrics_json = json.dumps(metrics, ensure_ascii=False)
        run.config_json = json.dumps(req.model_dump(), ensure_ascii=False)
        run.trades_json = json.dumps(result["trades"], ensure_ascii=False, default=str)
        run.equity_json = json.dumps(result["equity_curve"], ensure_ascii=False, default=str)
        session.commit()

        return {
            "ok": True,
            "run_id": run_id,
            "metrics": metrics,
            "trades": result["trades"],
            "equity_curve": result["equity_curve"],
        }
    except Exception as e:
        try:
            if run:
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = datetime.utcnow()
                session.commit()
        except Exception:
            pass
        return {"ok": False, "error": str(e), "traceback": traceback.format_exc()}
    finally:
        session.close()


@router.get("/runs")
def list_runs(limit: int = Query(20, ge=1, le=100)):
    """历史回测列表"""
    session = get_sync_session()
    try:
        rows = (
            session.query(BacktestRun)
            .order_by(BacktestRun.started_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "strategy_name": r.strategy_name,
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "data_count": r.data_count,
                "status": r.status,
                "total_return_pct": r.total_return_pct,
                "win_rate": r.win_rate,
                "profit_factor": r.profit_factor,
                "max_drawdown_pct": r.max_drawdown_pct,
                "sharpe_ratio": r.sharpe_ratio,
                "total_trades": r.total_trades,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in rows
        ]
    finally:
        session.close()


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    """单次回测详情"""
    session = get_sync_session()
    try:
        r = session.query(BacktestRun).filter_by(id=run_id).first()
        if not r:
            return {"ok": False, "error": "未找到该回测记录"}

        trades = json.loads(r.trades_json) if r.trades_json else []
        equity = json.loads(r.equity_json) if r.equity_json else []

        return {
            "ok": True,
            "id": r.id,
            "strategy_name": r.strategy_name,
            "symbol": r.symbol,
            "timeframe": r.timeframe,
            "data_count": r.data_count,
            "warmup": r.warmup,
            "status": r.status,
            "initial_capital": r.initial_capital,
            "final_equity": r.final_equity,
            "total_return_pct": r.total_return_pct,
            "win_rate": r.win_rate,
            "profit_factor": r.profit_factor,
            "max_drawdown_pct": r.max_drawdown_pct,
            "sharpe_ratio": r.sharpe_ratio,
            "total_trades": r.total_trades,
            "winning_trades": r.winning_trades,
            "losing_trades": r.losing_trades,
            "avg_trade_pnl": r.avg_trade_pnl,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "error_message": r.error_message,
            "trades": trades,
            "equity_curve": equity,
        }
    finally:
        session.close()
