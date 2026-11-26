"""应用入口：挂载路由、静态封面、CORS、统一错误格式。

启动： uvicorn app.main:app --reload --port 8000
文档： http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from . import config
from .db import Base, SessionLocal, engine, ensure_columns
from .errors import ApiError
from .models import Playlist, Song, User
from .routers import (
    assets,
    auth,
    browse,
    downloads,
    favorites,
    me,
    player,
    playlists,
    recent,
    search,
    songs,
)
from .schemas import HealthOut
from .seed import ensure_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    ensure_columns()
    ensure_seed()
    yield


app = FastAPI(
    title=config.APP_NAME,
    version=config.VERSION,
    description=(
        "韵律音乐 App 后端接口，响应字段与前端 data/*.json 保持一致。\n\n"
        "鉴权：先调用 `POST /auth/register` 或 `POST /auth/login` 拿 token，"
        "再点右上角 Authorize 填入即可调试需要登录的接口。"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


for module in (
    auth,
    songs,
    playlists,
    browse,
    search,
    player,
    favorites,
    recent,
    downloads,
    me,
    assets,
):
    app.include_router(module.router, prefix=config.API_PREFIX)


if config.COVER_DIR.exists():
    app.mount("/covers", StaticFiles(directory=config.COVER_DIR), name="covers")


@app.get("/health", response_model=HealthOut, tags=["meta"], summary="健康检查")
def health() -> dict:
    with SessionLocal() as db:
        return {
            "status": "ok",
            "version": config.VERSION,
            "songs": db.scalar(select(func.count()).select_from(Song)) or 0,
            "playlists": db.scalar(select(func.count()).select_from(Playlist)) or 0,
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
        }


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse(url="/docs")
