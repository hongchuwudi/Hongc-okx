"""
创建时间: 2026-06-08
作者: hongchuwudi
描述: 回测业务逻辑 — 同步 / 流式 / 异步执行 + 历史查询

包含:
- 类: BacktestService — 回测服务（run / run_stream / run_async / list / detail）
- 函数: _push_sync — WebSocket 消息推送
"""

import json
import threading
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import get_sync_session
from app.entities.backtest import BacktestRun
from app.core.exceptions import NotFoundError, ExternalServiceError, AppError
from app.core.logger import get_logger
from app.services.backtest.serializer import run_summary, run_detail
from app.services.backtest.executor import (
    _ensure_run, _build_strategy, _save_run_result, _config_json,
)

logger = get_logger()


# 回测服务 — 提供同步、流式、异步三种执行模式及历史查询
class BacktestService:

    # 同步执行回测 — 拉取 OKX 数据 → 初始化策略 → 运行引擎 → 写入数据库
    def run(
        self, strategy: str, symbol: str, timeframe: str,
        initial_capital: float, position_ratio: float, fee_rate: float,
        warmup: int, data_limit: int, temperature: float = 0.1,
        pre_run: BacktestRun | None = None,
    ) -> dict:
        # 获取同步数据库会话
        session: Session = get_sync_session()
        run: Optional[BacktestRun] = None
        try:
            # 创建或合并运行记录
            run, run_id = _ensure_run(session, strategy, symbol, timeframe,
                                      initial_capital, position_ratio, fee_rate,
                                      data_limit, warmup, pre_run=pre_run)

            # 从 OKX 拉取历史 K 线数据
            from app.exchange.client import get_okx_ohlcv
            ohlcv = get_okx_ohlcv(symbol, timeframe, data_limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            # 根据策略类型构建策略实例
            strategy_instance, data_limit = _build_strategy(strategy, symbol, timeframe, data_limit, temperature)
            run.data_count = data_limit

            # 运行回测引擎
            from app.services.backtest.engine import run_backtest as _run
            result = _run(df, strategy_instance,
                          initial_capital=initial_capital, position_ratio=position_ratio,
                          fee_rate=fee_rate, warmup=warmup, timeframe=timeframe)
            metrics = result["metrics"]

            # 将回测结果写入数据库
            _save_run_result(
                run, metrics,
                trades_json=json.dumps(result["trades"], ensure_ascii=False, default=str),
                equity_json=json.dumps(result["equity_curve"], ensure_ascii=False, default=str),
                config_json=_config_json(strategy, symbol, timeframe,
                                         initial_capital, position_ratio, fee_rate,
                                         warmup, data_limit),
                session=session,
            )

            # 返回结果供 API 直接使用
            return {
                "ok": True, "run_id": run_id,
                "metrics": metrics, "trades": result["trades"],
                "equity_curve": result["equity_curve"],
            }
        except Exception as e:
            # 异常时标记运行记录为失败
            try:
                if run:
                    run.status = "failed"
                    run.error_message = str(e)
                    run.finished_at = datetime.utcnow()
                    session.commit()
            except Exception:
                pass
            if isinstance(e, AppError):
                raise
            raise ExternalServiceError(str(e)) from e
        finally:
            session.close()

    # 流式执行回测 — 引擎在独立线程运行，主线程从队列取事件 + 心跳保活
    # LLM API 调用可能阻塞 10-30 秒，心跳防止 SSE 连接超时断开
    def run_stream(
        self, strategy: str, symbol: str, timeframe: str,
        initial_capital: float, position_ratio: float, fee_rate: float,
        warmup: int, data_limit: int, temperature: float = 0.1,
    ):
        import json as _json
        import queue

        # 获取同步数据库会话
        session: Session = get_sync_session()
        run: Optional[BacktestRun] = None
        engine_thread = None
        try:
            # 创建运行记录
            run, run_id = _ensure_run(session, strategy, symbol, timeframe,
                                      initial_capital, position_ratio, fee_rate,
                                      data_limit, warmup)

            # 从 OKX 拉取历史 K 线数据
            from app.exchange.client import get_okx_ohlcv
            ohlcv = get_okx_ohlcv(symbol, timeframe, data_limit)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            # 构建策略实例
            strategy_instance, data_limit = _build_strategy(strategy, symbol, timeframe, data_limit, temperature)
            run.data_count = data_limit

            from app.services.backtest.engine import run_backtest_stream

            # 引擎在独立线程运行，通过队列传递事件
            event_queue: queue.Queue = queue.Queue()

            # 后台线程：运行流式回测引擎，将事件写入队列
            def _run_engine():
                try:
                    for event in run_backtest_stream(
                        df, strategy_instance,
                        initial_capital=initial_capital, position_ratio=position_ratio,
                        fee_rate=fee_rate, warmup=warmup, timeframe=timeframe,
                    ):
                        event_queue.put(event)
                except Exception as e:
                    logger.warning(f"回测 #{run_id} 引擎异常: {e}")
                    event_queue.put({"type": "error", "message": str(e)})
                finally:
                    event_queue.put(None)  # 哨兵值，表示引擎结束

            engine_thread = threading.Thread(target=_run_engine, daemon=True)
            engine_thread.start()

            # 主循环：从队列取事件，15 秒无数据则发心跳保活
            while True:
                try:
                    event = event_queue.get(timeout=15)
                except queue.Empty:
                    yield ": heartbeat\n\n"
                    continue

                if event is None:  # 哨兵：引擎已结束，队列已清空
                    break

                yield f"data: {_json.dumps(event, ensure_ascii=False, default=str)}\n\n"

                # 回测完成事件：保存结果到数据库
                if event["type"] == "done":
                    metrics = event["metrics"]
                    _save_run_result(
                        run, metrics,
                        trades_json=_json.dumps(event["trades"], ensure_ascii=False, default=str),
                        equity_json=_json.dumps(event["equity_curve"], ensure_ascii=False, default=str),
                        config_json=_config_json(strategy, symbol, timeframe,
                                                 initial_capital, position_ratio, fee_rate,
                                                 warmup, data_limit),
                        session=session,
                    )
                    logger.info(f"回测 #{run_id} 完成: 交易{len(event['trades'])}笔, 权益{metrics['final_equity']:.2f}")

                # 错误事件：标记运行记录为失败
                elif event["type"] == "error":
                    run.status = "failed"
                    run.error_message = event.get("message", "")
                    run.finished_at = datetime.utcnow()
                    session.commit()

            engine_thread.join(timeout=5)

        except Exception as e:
            # 外层异常处理：标记失败并返回错误事件
            try:
                if run:
                    run.status = "failed"
                    run.error_message = str(e)
                    run.finished_at = datetime.utcnow()
                    session.commit()
            except Exception:
                pass
            yield f"data: {_json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            session.close()

    # 异步执行回测 — 立即返回 run_id，后台线程运行并推送进度到 WebSocket
    def run_async(
        self, strategy: str, symbol: str, timeframe: str,
        initial_capital: float, position_ratio: float, fee_rate: float,
        warmup: int, data_limit: int, temperature: float = 0.1,
    ) -> dict:
        # 先创建运行记录并立即返回
        session = get_sync_session()
        run = BacktestRun(
            strategy_name=strategy, symbol=symbol, timeframe=timeframe,
            initial_capital=initial_capital, position_ratio=position_ratio,
            fee_rate=fee_rate, data_count=data_limit, warmup=warmup,
            status="running", started_at=datetime.utcnow(),
        )
        session.add(run)
        session.commit()
        run_id = run.id
        session.close()

        # 后台线程执行回测
        def _bg():
            try:
                logger.info(f"回测 #{run_id} 后台线程启动")
                result = self.run(strategy, symbol, timeframe, initial_capital,
                                 position_ratio, fee_rate, warmup, data_limit, temperature, pre_run=run)
                # 推送完成通知到 WebSocket
                _push_sync({"type": "backtest_done", "run_id": run_id,
                           "metrics": result.get("metrics"), "trades_count": len(result.get("trades", []))})
            except Exception as e:
                logger.error(f"回测 #{run_id} 异常: {e}")
                # 推送错误通知到 WebSocket
                _push_sync({"type": "backtest_error", "run_id": run_id, "error": str(e)})

        threading.Thread(target=_bg, daemon=True).start()
        return {"ok": True, "run_id": run_id, "status": "started"}

    # 查询回测运行记录列表（按时间倒序，支持分页）
    def list_runs(self, page: int = 1, page_size: int = 20) -> dict:
        session = get_sync_session()
        try:
            # 计算总记录数和分页信息
            total = session.query(BacktestRun).count()
            offset = (page - 1) * page_size
            rows = (
                session.query(BacktestRun)
                .order_by(BacktestRun.started_at.desc())
                .offset(offset).limit(page_size).all()
            )
            # 返回分页数据，每条记录转为摘要 dict
            return {
                "data": [run_summary(r) for r in rows],
                "page": page, "page_size": page_size,
                "total": total,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            }
        finally:
            session.close()

    # 查询单次回测的完整详情
    def get_run_detail(self, run_id: int) -> dict:
        session = get_sync_session()
        try:
            r = session.query(BacktestRun).filter_by(id=run_id).first()
            if not r:
                raise NotFoundError(f"回测记录 #{run_id} 不存在")
            # 返回完整详情，含交易列表和权益曲线
            return run_detail(r)
        finally:
            session.close()


# WebSocket 消息推送 — 通过 Redis Pub/Sub 广播事件给前端
def _push_sync(event: dict):
    try:
        import json as _json
        from app.core.database import redis_publish
        # 将事件序列化后发布到 Redis 频道
        redis_publish("ws:channel:updates", _json.dumps(event, ensure_ascii=False, default=str))
        logger.info(f"WS推送: {event.get('type')} run_id={event.get('run_id')}")
    except Exception as e:
        logger.warning(f"WS推送失败: {e}")


# 全局单例
backtest_service = BacktestService()