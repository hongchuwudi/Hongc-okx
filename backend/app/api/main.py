"""FastAPI 应用入口"""

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

app = FastAPI(title="Trading Platform API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(trades_router)
app.include_router(strategies_router)
app.include_router(backtest_router)
app.include_router(ws_router)

# 生产模式：serve React 构建产物
_proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_dist_dir = os.path.join(_proj_root, "frontend", "dist")
if os.path.isdir(_dist_dir):
    @app.get("/")
    async def serve_index():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(_dist_dir, "index.html"))

    app.mount("/assets", StaticFiles(directory=os.path.join(_dist_dir, "assets")), name="assets")


@app.on_event("startup")
async def startup():
    init_db()
