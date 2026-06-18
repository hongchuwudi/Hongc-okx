"""
创建时间: 2026-06-06
作者: hongchuwudi
描述: FastAPI 应用入口 — 注册路由、中间件、静态文件服务，启动时初始化数据库

包含:
- 函数: serve_index — 生产模式提供 React 前端首页
- 函数: startup — 应用启动时初始化数据库表
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.strategies import router as strategies_router
from app.api.v1.trades import router as trades_router
from app.api.v1.backtest import router as backtest_router
from app.api.v1.agents import router as agents_router
from app.api.v1.config import router as config_router
from app.api.ws import router as ws_router
from app.core.database import init_db
from app.core.exceptions import AppError
from app.core.logger import get_logger

_logger = get_logger()

# 创建 FastAPI 应用实例
app = FastAPI(title="Trading Platform API", version="2.0.0")

# CORS 中间件 — 允许前端 dev server 跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 全局异常处理器 ============================================================

# AppError → JSON 响应，根据 status_code 返回对应 HTTP 状态码
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": exc.message, "detail": exc.detail},
    )

# AppError 及其子类 → 自动读取 exc.status_code
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    if exc.status_code >= 500:
        _logger.error(f"{type(exc).__name__}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": exc.message, "detail": exc.detail},
    )

# 兜底：未捕获的 Exception → 500
@app.exception_handler(Exception)
async def unhandled_handler(request, exc: Exception):
    _logger.error(f"未处理异常: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": "服务器内部错误"},
    )

# 注册所有路由
app.include_router(dashboard_router)        # /api/status, /api/health, /api/equity
app.include_router(trades_router)           # /api/trades
app.include_router(strategies_router)       # /api/strategies
app.include_router(backtest_router)         # /api/backtest/*
app.include_router(agents_router)           # /api/agents/status
app.include_router(config_router)           # /api/config
app.include_router(ws_router)               # /ws/live

# 生产模式：serve React 前端构建产物
_proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_dist_dir = os.path.join(_proj_root, "frontend", "dist")
if os.path.isdir(_dist_dir):
    # 生产模式：提供 React 前端首页
    @app.get("/")
    async def serve_index():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(_dist_dir, "index.html"))

    # 挂载静态资源目录
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist_dir, "assets")), name="assets")

# 应用启动时创建数据库表 + 启动 WebSocket 监听器
@app.on_event("startup")
async def startup():
    init_db()
    # 提前启动 Redis Pub/Sub 监听器，避免前端连接前消息丢失
    from app.api.ws import _ensure_listener
    await _ensure_listener()
