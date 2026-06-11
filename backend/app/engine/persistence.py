"""
创建时间: 2026-06-08
作者: hongchuwudi
文件名: persistence_service.py 持久化服务
描述: Tick 完成后的持久化操作 — PostgreSQL 写入 + Redis 缓存 + Pub/Sub 事件推送

包含:
- 类: PersistenceService — 持久化服务（DB写入/Redis缓存/事件推送）
"""

import asyncio
import json
from datetime import datetime

from app.config import config
from app.database import SyncSession, get_redis, get_sync_session
from app.entities.system import SystemStatus
from app.entities.trading import EquitySnapshot, Trade
from app.core.logger import get_logger

logger = get_logger()


# 清理 LLM 输出中的破损 Unicode (lone surrogates)
def _clean(s: str) -> str:
    return s.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')


# Tick 持久化服务 — 封装 PostgreSQL 写入、Redis 信号缓存和事件推送
class PersistenceService:

    # 写入 tick 结果到 PostgreSQL（在线程池中执行，避免阻塞事件循环）
    async def persist_tick(
        self, price: float, account: dict, position: dict | None,
        signal, trade_result: dict | None,
    ) -> None:
        def _write_db():
            sess: SyncSession = get_sync_session()
            try:
                row = sess.query(SystemStatus).filter_by(id=1).first()
                if row is None:
                    row = SystemStatus(id=1)
                    sess.add(row)
                row.status = "running"
                row.last_update = datetime.now()
                row.balance = account["balance"]
                row.equity = account["equity"]
                row.btc_price = price
                row.ai_signal = signal.signal
                row.ai_confidence = signal.confidence
                row.ai_reason = signal.reason
                if hasattr(signal, 'agent_reports') and signal.agent_reports:
                    cleaned = {k: _clean(v) for k, v in signal.agent_reports.items()}
                    row.ai_reason = json.dumps(
                        {"reason": _clean(signal.reason), "agents": cleaned},
                        ensure_ascii=False
                    )
                row.ai_stop_loss = float(signal.stop_loss)
                row.ai_take_profit = float(signal.take_profit)
                row.ai_timestamp = datetime.now()
                row.timeframe = config.trade.timeframe
                # 读取运行时 agent_mode（Redis 优先，env fallback）
                try:
                    from app.services.config.runtime import get_runtime
                    row.agent_mode = get_runtime("agent_mode")
                except Exception:
                    row.agent_mode = config.trade.agent_mode
                if position:
                    row.position_side = position["side"]
                    row.position_size = position["size"]
                    row.position_entry_price = position["entry_price"]
                    row.position_unrealized_pnl = position.get("unrealized_pnl", 0)
                    row.position_mark_price = position.get("mark_price", 0)
                    row.position_pnl_pct = position.get("pnl_pct", 0)
                    row.position_margin = position.get("margin", 0)
                    row.position_notional = position.get("notional", 0)
                    row.position_liquidation_price = position.get("liquidation_price", 0)
                else:
                    row.position_side = None
                    row.position_size = 0
                    row.position_entry_price = 0
                    row.position_unrealized_pnl = 0
                    row.position_mark_price = 0
                    row.position_pnl_pct = 0
                    row.position_margin = 0
                    row.position_notional = 0
                    row.position_liquidation_price = 0
                sess.commit()

                snap = EquitySnapshot(timestamp=datetime.now(), equity=account["equity"])
                sess.add(snap)
                sess.commit()

                if trade_result:
                    trade = Trade(
                        timestamp=datetime.now(), signal=signal.signal,
                        price=price, amount=trade_result.get("amount", 0),
                        confidence=signal.confidence, reason=signal.reason, pnl=0,
                    )
                    sess.add(trade)
                    sess.commit()
            except Exception as e:
                logger.error(f"数据持久化失败: {e}")
                sess.rollback()
            finally:
                sess.close()

        await asyncio.get_event_loop().run_in_executor(None, _write_db)

    # 更新 Redis 信号缓存（最新信号 + 历史列表）
    async def cache_signal(self, signal) -> None:
        try:
            redis = await get_redis()
            await redis.hset("signal:btc:latest", mapping={
                "signal": signal.signal, "confidence": signal.confidence,
                "reason": signal.reason, "stop_loss": str(signal.stop_loss),
                "take_profit": str(signal.take_profit),
                "timestamp": datetime.now().isoformat(),
            })
            await redis.expire("signal:btc:latest", 300)
            await redis.lpush("signal:btc:history", json.dumps({
                "signal": signal.signal, "confidence": signal.confidence,
                "timestamp": datetime.now().isoformat(),
            }))
            await redis.ltrim("signal:btc:history", 0, 49)
        except Exception as e:
            logger.error(f"Redis 缓存更新失败: {e}")

    # 发布事件到 Redis Pub/Sub 频道，供 WebSocket 推送到前端
    async def publish_event(self, data: dict) -> None:
        try:
            redis = await get_redis()
            await redis.publish("ws:channel:updates", json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"事件推送失败: {e}")


# 全局单例
persistence_service = PersistenceService()

# 模块级包装函数 — 供 engine 直接 import 使用
persist_tick = persistence_service.persist_tick
cache_signal = persistence_service.cache_signal
publish_event = persistence_service.publish_event
