"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: ws.py WebSocket实时推送
描述: WebSocket 服务 — 共享单个 Redis Pub/Sub 连接，广播实时更新给所有浏览器客户端

包含:
- 函数: _ensure_listener — 确保单个 Redis 监听器后台任务运行
- 函数: _listen — Redis Pub/Sub 监听循环（异常自动重连）
- 函数: websocket_live — WebSocket 端点，接收客户端连接并处理 ping/pong 心跳
- 常量: _connections — 活跃的 WebSocket 连接集合
- 常量: _listener_task — 后台监听任务的引用
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import get_redis_pubsub
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger()

_connections: set[WebSocket] = set()
_listener_task: asyncio.Task | None = None


async def _ensure_listener():
    global _listener_task
    if _listener_task is None or _listener_task.done():
        _listener_task = asyncio.create_task(_listen())


async def _listen():
    """Redis Pub/Sub 监听循环，异常自动重连，永不退出。"""
    global _connections
    while True:
        pubsub = None
        try:
            redis = await get_redis_pubsub()
            pubsub = redis.pubsub()
            await pubsub.subscribe("ws:channel:updates")
            logger.info("[ws listen] 已订阅 Redis ws:channel:updates")
            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg is None:
                    continue
                if msg.get("type") == "message" and msg.get("data"):
                    data = msg["data"]
                    try:
                        info = json.loads(data)
                        t = info.get("type", "?")
                    except Exception:
                        t = "?"
                    stale: set[WebSocket] = set()
                    for ws in _connections:
                        try:
                            await ws.send_text(data)
                        except Exception:
                            stale.add(ws)
                    _connections -= stale
        except asyncio.CancelledError:
            logger.info("[ws listen] 任务取消")
            break
        except Exception as e:
            logger.error(f"[ws listen] 异常，3s 后重连: {type(e).__name__}: {e}")
            await asyncio.sleep(3)
        finally:
            if pubsub is not None:
                try:
                    await pubsub.unsubscribe("ws:channel:updates")
                except Exception:
                    pass
                try:
                    await pubsub.reset()
                except Exception:
                    pass


@router.websocket("/ws/v1/live")
async def websocket_live(ws: WebSocket):
    await ws.accept()
    _connections.add(ws)
    await _ensure_listener()

    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(ws)
