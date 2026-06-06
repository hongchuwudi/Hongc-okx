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
from fastapi.staticfiles import StaticFiles

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.strategies import router as strategies_router
from app.api.routes.trades import router as trades_router
from app.api.routes.backtest import router as backtest_router
from app.api.ws import router as ws_router
from app.database import init_db

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

# 注册所有路由
app.include_router(dashboard_router)        # /api/status, /api/health, /api/equity
app.include_router(trades_router)           # /api/trades
app.include_router(strategies_router)       # /api/strategies
app.include_router(backtest_router)         # /api/backtest/*
app.include_router(ws_router)               # /ws/live

# 生产模式：serve React 前端构建产物
_proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_dist_dir = os.path.join(_proj_root, "frontend", "dist")
if os.path.isdir(_dist_dir):
    @app.get("/")
    async def serve_index():
        """生产模式：提供 React 前端首页"""
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(_dist_dir, "index.html"))

    # 挂载静态资源目录
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist_dir, "assets")), name="assets")

@app.on_event("startup")
async def startup():
    """应用启动时创建数据库表"""
    init_db()
