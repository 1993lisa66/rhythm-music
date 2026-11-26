"""运行期配置。全部可用环境变量覆盖，避免改代码。"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SEED_DIR = BASE_DIR / "data" / "seed"
STATIC_DIR = BASE_DIR / "static"
COVER_DIR = STATIC_DIR / "covers"

APP_NAME = "韵律音乐 App API"
VERSION = "1.0.0"
API_PREFIX = os.getenv("RHYTHM_API_PREFIX", "/api/v1")

DATABASE_URL = os.getenv("RHYTHM_DATABASE_URL", f"sqlite:///{BASE_DIR / 'rhythm.db'}")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "RHYTHM_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
    ).split(",")
    if origin.strip()
]

# 与前端 design tokens 对齐的固定取值
QUALITIES = ("标准", "高品质", "无损")
REPEAT_MODES = ("all", "one", "off")

# 首屏对齐设计稿：晚风 01:28 / 03:42
DEFAULT_POSITION = 88
