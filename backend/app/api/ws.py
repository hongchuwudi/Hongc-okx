"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: ws.py WebSocket实时推送
描述: WebSocket 服务 — 共享单个 Redis Pub/Sub 连接，广播实时更新给所有浏览器客户端

包含:
- 函数: _ensure_listener — 确保单个 Redis 监听器后台任务运行
- 函数: _listen — Redis Pub/Sub 监听循环，广播消息给所有 WebSocket 客户端
- 函数: websocket_live — WebSocket 端点，接收客户端连接并处理 ping/pong 心跳
- 常量: _connections — 活跃的 WebSocket 连接集合
- 常量: _listener_task — 后台监听任务的引用
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import get_redis_pubsub

router = APIRouter()

_connections: set[WebSocket] = set()  # 活跃的 WebSocket 连接集合
_listener_task: asyncio.Task | None = None  # 后台 Redis 监听任务引用


async def _ensure_listener():
    """确保系统中只有一个 Redis Pub/Sub 监听器在运行"""
    global _listener_task
    if _listener_task is None or _listener_task.done():
        _listener_task = asyncio.create_task(_listen())


async def _listen():
    """单例后台任务：监听 Redis Pub/Sub 频道，广播消息给所有连接的 WebSocket 客户端"""
    try:
        redis = await get_redis_pubsub()
        pubsub = redis.pubsub()
        await pubsub.subscribe("ws:channel:updates")
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg.get("data"):
                stale: set[WebSocket] = set()  # 已断开的连接，稍后清理
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
    """WebSocket 端点：接受客户端连接，处理 ping/pong 心跳保持连接"""
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
