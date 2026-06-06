#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易平台 - 统一启动入口
同时启动: FastAPI API 服务器 + 交易引擎
"""

import asyncio
import sys
import threading
import warnings

import urllib3
import uvicorn

# 代理环境下抑制 SSL 警告刷屏
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

from app.database import init_db
from app.logger import get_logger

logger = get_logger()

# Uvicorn 日志配色 — INFO 级别不用红色，改用绿色
UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {
            "()": "logging.Formatter",
            "fmt": "%(levelname)-8s %(message)s",
        },
        "access": {
            "()": "logging.Formatter",
            "fmt": '%(levelname)-8s %(message)s',
        },
    },
    "handlers": {
        "plain": {"formatter": "plain", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"},
        "access": {"formatter": "access", "class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
    },
    "loggers": {
        "uvicorn": {"handlers": ["plain"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


def start_api():
    """启动 FastAPI 服务器（独立线程）"""
    uvicorn.run(
        "app.api.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
        log_config=UVICORN_LOG_CONFIG,
    )


async def start_engine():
    """启动交易引擎"""
    from app.engine.loop import TradingEngine
    engine = TradingEngine()
    await engine.run()


async def main():
    """主入口"""
    logger.info("=" * 60)
    logger.info("事件驱动交易平台 v2.0")
    logger.info("=" * 60)

    # 初始化数据库
    logger.info("初始化 PostgreSQL 连接...")
    init_db()
    logger.info("数据库表已就绪")

    # API 服务器（独立线程）
    api_thread = threading.Thread(target=start_api, daemon=True, name="APIServer")
    api_thread.start()
    logger.info("API 服务器: http://127.0.0.1:8765")
    logger.info("WebSocket: ws://127.0.0.1:8765/ws/live")

    # 交易引擎（主线程 asyncio）
    logger.info("启动交易引擎...")
    await start_engine()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
        sys.exit(0)
