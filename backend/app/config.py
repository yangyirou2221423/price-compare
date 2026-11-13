"""Application configuration and filesystem paths."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = Path(os.getenv("PRICECOMPARE_DATA_DIR", BACKEND_DIR / "data"))
DB_PATH = Path(os.getenv("PRICECOMPARE_DB_PATH", DATA_DIR / "pricecompare.db"))
SEED_PATH = Path(
    os.getenv("PRICECOMPARE_SEED_PATH", PROJECT_ROOT / "data" / "seed" / "catalog.json")
)
DATABASE_URL = os.getenv(
    "PRICECOMPARE_DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}"
)
DEMO_NOW = "2026-11-13"
ENGINE_VERSION = "0.1.0"

PLATFORMS = [
    {"id": "jd", "name": "京东", "short": "京东"},
    {"id": "taobao", "name": "淘宝", "short": "淘宝"},
    {"id": "pdd", "name": "拼多多", "short": "拼多多"},
    {"id": "douyin", "name": "抖音", "short": "抖音"},
]
REGIONS = ["全国", "浙江", "江苏", "上海", "广东", "北京", "四川", "湖北"]
MEMBERSHIPS = ["88VIP", "京东 PLUS", "拼多多省钱月卡"]
