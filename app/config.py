"""运行期配置。全部可用环境变量覆盖，避免改代码。"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """读取项目根目录的 .env（已被 .gitignore 忽略），不覆盖已存在的环境变量。"""
    path = BASE_DIR / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

SEED_DIR = BASE_DIR / "data" / "seed"
STATIC_DIR = BASE_DIR / "static"
COVER_DIR = STATIC_DIR / "covers"

APP_NAME = "韵律音乐 App API"
VERSION = "1.0.0"
API_PREFIX = os.getenv("RHYTHM_API_PREFIX", "/api/v1")

DATABASE_URL = os.getenv("RHYTHM_DATABASE_URL", f"sqlite:///{BASE_DIR / 'rhythm.db'}")

# 鉴权：生产环境务必用 RHYTHM_JWT_SECRET 覆盖（默认值仅供本地开发）
JWT_SECRET = os.getenv("RHYTHM_JWT_SECRET", "rhythm-dev-secret-change-me")
JWT_TTL_SECONDS = int(os.getenv("RHYTHM_JWT_TTL", str(7 * 24 * 3600)))
PASSWORD_MIN_LENGTH = 6

# 首次启动自动创建的演示账号（拥有设计稿里的完整数据）
DEMO_EMAIL = os.getenv("RHYTHM_DEMO_EMAIL", "demo@rhythm.app")
DEMO_PASSWORD = os.getenv("RHYTHM_DEMO_PASSWORD", "rhythm2026")
DEMO_NAME = os.getenv("RHYTHM_DEMO_NAME", "阿韵")


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

# 阿里云 OSS：静态资源（封面 / 音频）存储，密钥只从环境变量或 .env 读取
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")
OSS_BUCKET = os.getenv("OSS_BUCKET", "")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")
OSS_PUBLIC_BASE = os.getenv("OSS_PUBLIC_BASE", "")


def oss_ready() -> bool:
    return all((OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET, OSS_ENDPOINT))


def public_asset(path: str) -> str:
    """库里的 /covers/x.jpg 换成 OSS 公共地址；未配置 OSS_PUBLIC_BASE 时原样返回。

    前端只认一个 cover 字段，所以换源只在服务端做，接口形状不变。
    """
    if not path or path.startswith(("http://", "https://", "data:")):
        return path
    base = OSS_PUBLIC_BASE.strip().rstrip("/")
    if not base:
        return path
    return f"{base}/{path.lstrip('/')}"

