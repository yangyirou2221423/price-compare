"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import catalog, history, strategy
from app.config import ENGINE_VERSION, SEED_PATH
from app.db.seed import bootstrap

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap()
    yield


app = FastAPI(
    title="价策 · 智能比价与购买策略 API",
    version=ENGINE_VERSION,
    description=(
        "演示型比价与优惠叠加求解服务。所有价格均为模拟数据，"
        "国补与平台规则为可配置示例，不进行页面抓取。"
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(strategy.router)
app.include_router(history.router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "engine_version": ENGINE_VERSION,
        "seed_exists": SEED_PATH.exists(),
        "data_source": "mock",
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "价策 · 智能比价与购买策略",
        "version": ENGINE_VERSION,
        "docs": "/docs",
        "note": "演示数据；不抓取平台页面。",
    }
