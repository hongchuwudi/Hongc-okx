#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建时间: 2026-06-06
作者: hongchuwudi
文件名: run.py 统一启动器
描述: 交易平台启动入口 — 环境检查 → 缓存清理 → 数据库初始化 → API 服务 → 交易引擎

包含:
- 函数: clean_pycache — 清理 Python 字节码缓存
- 函数: check_env — 检查必要的环境配置
- 函数: start_api — 在独立线程中启动 FastAPI (uvicorn)
- 函数: start_engine — 启动交易引擎主循环
- 函数: shutdown — 优雅关闭
- 函数: main — 主入口
- 常量: BANNER — 启动横幅
- 常量: UVICORN_LOG_CONFIG — Uvicorn 日志格式
"""

import asyncio
import os
import pathlib
import shutil
import signal
import sys
import threading
import warnings

import urllib3
import uvicorn

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

from app.logger import get_logger

logger = get_logger()

# ── 启动横幅 ─────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════╗
║       BTC/USDT 永续合约 AI 交易系统 v2.0      ║
║        4 Agent 串行决策 · DeepSeek · OKX       ║
╚══════════════════════════════════════════════╝
"""

# ── Uvicorn 日志配置 ─────────────────────────────────────────

UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"()": "logging.Formatter", "fmt": "%(levelname)-8s %(message)s"},
        "access": {"()": "logging.Formatter", "fmt": "%(levelname)-8s %(message)s"},
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

# ── 信号处理 ─────────────────────────────────────────────────

_shutdown_event = asyncio.Event()


def _handle_signal(signum, frame):
    """处理 SIGINT/SIGTERM，触发优雅关闭。"""
    logger.info(f"收到信号 {signum}，正在优雅关闭...")
    _shutdown_event.set()


# ── 缓存清理 ─────────────────────────────────────────────────

def clean_pycache():
    """清理所有 __pycache__ 和 .pyc 文件，防止旧字节码缓存导致修改不生效。"""
    root = pathlib.Path(__file__).resolve().parent
    count = 0
    for cache_dir in root.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            count += 1
        except Exception:
            pass
    for pyc in root.rglob("*.pyc"):
        try:
            pyc.unlink()
            count += 1
        except Exception:
            pass
    if count:
        logger.info(f"已清理 {count} 个缓存文件/目录")


# ── 环境检查 ─────────────────────────────────────────────────

def check_env():
    """检查必要环境配置，缺失则给出明确提示。"""
    issues = []

    # 检查 .env 文件
    env_path = pathlib.Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        issues.append(".env 文件不存在，请从 .env_template 复制并配置")
    else:
        # 检查关键配置项
        from app.config import config as cfg
        if not cfg.ai.deepseek_api_key or "your-" in cfg.ai.deepseek_api_key:
            issues.append("DEEPSEEK_API_KEY 未配置，AI 决策将不可用")
        if not cfg.okx.api_key or "your-" in cfg.okx.api_key:
            issues.append("OKX_API_KEY 未配置，交易所连接将失败")

    # 检查 data 目录
    data_dir = pathlib.Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)

    if issues:
        logger.warning("=" * 50)
        logger.warning("环境检查发现问题:")
        for i in issues:
            logger.warning(f"  ! {i}")
        logger.warning("=" * 50)

    return len(issues) == 0


# ── API 服务器 ───────────────────────────────────────────────

def start_api():
    """在独立守护线程中启动 FastAPI 服务器。"""
    uvicorn.run(
        "app.api.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
        log_config=UVICORN_LOG_CONFIG,
    )


# ── 交易引擎 ─────────────────────────────────────────────────

async def start_engine():
    """启动交易引擎主循环，监听关闭事件。"""
    from app.engine.loop import TradingEngine

    engine = TradingEngine()

    # 并行运行引擎和关闭等待
    engine_task = asyncio.create_task(engine.run())
    shutdown_task = asyncio.create_task(_shutdown_event.wait())

    done, pending = await asyncio.wait(
        [engine_task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # 取消未完成的任务
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    logger.info("交易引擎已停止")


# ── 主入口 ───────────────────────────────────────────────────

async def main():
    """启动流程：缓存清理 → 环境检查 → 数据库初始化 → API → 交易引擎。"""
    # 阶段 0: 启动前准备
    logger.info(BANNER)
    clean_pycache()
    check_env()

    # 阶段 1: 数据库
    logger.info("[1/3] 初始化数据库...")
    try:
        from app.database import init_db
        init_db()
        logger.info("      数据库就绪")
    except Exception as e:
        logger.error(f"      数据库初始化失败: {e}")
        logger.error("      请检查 PostgreSQL/Redis 是否运行，以及 .env 配置是否正确")
        sys.exit(1)

    # 阶段 2: API 服务器
    logger.info("[2/3] 启动 API 服务器...")
    api_thread = threading.Thread(target=start_api, daemon=True, name="APIServer")
    api_thread.start()
    logger.info("      http://127.0.0.1:8765")
    logger.info("      WebSocket: ws://127.0.0.1:8765/ws/live")
    await asyncio.sleep(0.5)  # 等 uvicorn 完成首次绑定

    # 阶段 3: 交易引擎
    logger.info("[3/3] 启动交易引擎...")
    try:
        await start_engine()
    except Exception as e:
        logger.error(f"交易引擎异常退出: {e}")
    finally:
        logger.info("系统已关闭")


if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)
