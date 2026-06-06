"""WebSocket — 共享单个 Redis Pub/Sub 连接广播给所有客户端"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import get_redis_pubsub

router = APIRouter()

_connections: set[WebSocket] = set()
_listener_task: asyncio.Task | None = None


async def _ensure_listener():
    """确保只有一个 Redis 监听器在运行"""
    global _listener_task
    if _listener_task is None or _listener_task.done():
        _listener_task = asyncio.create_task(_listen())


async def _listen():
    """单例 Redis Pub/Sub 监听，广播给所有 WebSocket"""
    try:
        redis = await get_redis_pubsub()
        pubsub = redis.pubsub()
        await pubsub.subscribe("ws:channel:updates")
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                stale: set[WebSocket] = set()
                for ws in _connections:
                    try:
                        await ws.send_text(msg["data"])
                    except Exception:
                        stale.add(ws)
                _connections -= stale
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


@router.websocket("/ws/live")
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
