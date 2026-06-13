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
import warnings

sys.tracebacklimit = 0

import urllib3
import uvicorn

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

from app.core.logger import get_logger, shutdown_logging

logger = get_logger()

# ── 启动横幅 ─────────────────────────────────────────────────

C = '\033[96m'   # 青色
Y = '\033[93m'   # 黄色
W = '\033[97m'   # 白色
BOLD = '\033[1m'
RESET = '\033[0m'

BANNER = f"""
{C}{BOLD}
  ██╗  ██╗ ██████╗ ███╗   ██╗ ██████╗  ██████╗    ██████╗ ██╗  ██╗██╗  ██╗
  ██║  ██║██╔═══██╗████╗  ██║██╔════╝ ██╔════╝    ██╔══██╗██║ ██╔╝╚██╗██╔╝
  ███████║██║   ██║██╔██╗ ██║██║  ███╗██║         ██║  ██║█████╔╝  ╚███╔╝
  ██╔══██║██║   ██║██║╚██╗██║██║   ██║██║         ██║  ██║██╔═██╗  ██╔██╗
  ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝╚██████╗    ██████╔╝██║  ██╗██╔╝ ██╗
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝  ╚═════╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
{RESET}
{Y}{BOLD}  Virtual Currency(BTC/DOGE) · Perpetual Swap AI Trading System v2.0
  {W}⚡ 5/3/1 solo Agent Parallel  ·  DeepSeek/qwen  ·  OKX{RESET}
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


# 处理 SIGINT/SIGTERM，触发优雅关闭。
def _handle_signal(signum, frame):
    logger.info(f"收到信号 {signum}，正在优雅关闭...")
    _shutdown_event.set()


# ── 缓存清理 ─────────────────────────────────────────────────

# 清理所有 __pycache__ 和 .pyc 文件，防止旧字节码缓存导致修改不生效。
def clean_pycache():
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

# 检查必要环境配置，缺失则给出明确提示。
def check_env():
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


# ── 交易引擎 ─────────────────────────────────────────────────

# 启动交易引擎主循环，监听关闭事件。
async def start_engine():
    from app.engine.loop import TradingEngine
    from app.services.engine.engine_control import set_running

    engine = TradingEngine()
    set_running(engine.scheduler)

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

# 启动流程：缓存清理 → 环境检查 → 数据库初始化 → API → 交易引擎。
async def main():
    # 阶段 0: 启动前准备
    logger.info(BANNER)
    clean_pycache()
    check_env()

    # 阶段 0.5: 打印运行配置摘要（Redis 优先，env 兜底，标注来源）
    from app.services.config.runtime import get_runtime_sources, sync_runtime_to_env
    sources = get_runtime_sources()
    # 取有效值（Redis 优先）
    rt = {k: v["value"] for k, v in sources.items()}
    # 来源标记
    def _tag(k): return "[R]" if sources[k]["source"] == "redis" else "[E]"
    sandbox_label = "模拟盘 (DEMO)" if rt.get("sandbox", True) else "实盘 (MAIN)"
    auto_start_label = "是" if rt.get("agent_auto_start", False) else "否"
    agent_mode_map = {"5_agent": "5 Agent 完整", "3_agent": "3 Agent 快速", "1_agent": "1 Agent 急速", "tech": "纯技术指标"}
    logger.info("-" * 44)
    logger.info(f"  交易模式 : {_tag('sandbox')} {sandbox_label}")
    logger.info(f"  交易对   : {_tag('symbol')} {rt.get('symbol')}")
    logger.info(f"  杠杆     : {_tag('leverage')} {rt.get('leverage')}x")
    logger.info(f"  K线周期 : {_tag('timeframe')} {rt.get('timeframe')}")
    logger.info(f"  Tick间隔: {_tag('tick_interval_seconds')} {rt.get('tick_interval_seconds')}s")
    logger.info(f"  下单金额 : {_tag('order_amount')} {rt.get('order_amount')} USDT")
    logger.info(f"  Agent模式: {_tag('agent_mode')} {agent_mode_map.get(rt.get('agent_mode', ''), rt.get('agent_mode'))}")
    logger.info(f"  自动启动 : {_tag('agent_auto_start')} {auto_start_label}")
    logger.info(f"  日回撤上限: {_tag('max_daily_drawdown_pct')} {rt.get('max_daily_drawdown_pct')}%")
    logger.info(f"  日亏损上限: {_tag('max_daily_loss_usdt')} {rt.get('max_daily_loss_usdt')} USDT")
    logger.info(f"  仓位上限 : {_tag('max_position_ratio')} {float(rt.get('max_position_ratio', 0.8)) * 100:.0f}%")
    logger.info("-" * 44)
    # Redis 有值且与 env 不同 → 自动同步回 .env
    sync_msg = sync_runtime_to_env()
    if sync_msg:
        logger.info(sync_msg)
    from app.config import config as cfg

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

        # 阶段 2: API 服务器（asyncio 任务，Ctrl+C 一起退出）
    logger.info("[2/3] 启动 API 服务器...")
    api_srv = uvicorn.Server(uvicorn.Config(
        "app.api.main:app", host="127.0.0.1", port=8765,
        log_level="info", log_config=UVICORN_LOG_CONFIG,
    ))
    api_task = asyncio.create_task(api_srv.serve())
    await asyncio.sleep(0.5)
    logger.info("      http://127.0.0.1:8765")
    logger.info("      WebSocket: ws://127.0.0.1:8765/ws/live")

    # 阶段 3: 交易引擎
    try:
        if cfg.trade.agent_auto_start:
            logger.info("[3/3] 启动交易引擎...")
            logger.info("      引擎状态: 运行中")
            engine_task = asyncio.create_task(start_engine())
        else:
            logger.info("[3/3] 跳过自动启动（AGENT_AUTO_START=false）")
            logger.info("      引擎状态: 未启动 (可通过前端 UI 或 API 手动启动)")
            logger.info("      API: POST /api/v1/engine/start")
            logger.info("      访问 http://127.0.0.1:8765")
            engine_task = asyncio.create_task(_shutdown_event.wait())

        # 等引擎或关闭信号
        await engine_task
    finally:
        # 关闭 API 服务器
        api_srv.should_exit = True
        api_task.cancel()
        try:
            await api_task
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        logger.info("系统已关闭")
        shutdown_logging()


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
    finally:
        shutdown_logging()
