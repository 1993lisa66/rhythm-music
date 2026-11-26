"""运行期配置。全部可用环境变量覆盖，避免改代码。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from pathlib import Path
from urllib.parse import quote

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

# 阿里云 OSS：静态资源（封面 / 音频）存储，密钥只从环境变量或 .env 读取。
# Bucket 为私有读，所有资源地址都由后端现签（URL 带 Expires + Signature），
# 前端拿到的依旧是普通字符串，接口形状不变。
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")
OSS_BUCKET = os.getenv("OSS_BUCKET", "")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "")
# 自定义域名 / CDN（可选）；不填则用 <bucket>.<endpoint>。兼容旧的 OSS_PUBLIC_BASE 名字。
OSS_ASSET_HOST = os.getenv("OSS_ASSET_HOST") or os.getenv("OSS_PUBLIC_BASE", "")
# 签名有效期（秒），默认 6 小时
OSS_URL_TTL = int(os.getenv("OSS_URL_TTL", str(6 * 3600)))
# 过期时间对齐粒度：同一窗口内签出的地址完全一致，浏览器缓存才能命中
OSS_URL_ALIGN = int(os.getenv("OSS_URL_ALIGN", "1800"))
# 换签接口只接受这些前缀的对象键，避免被用来签任意私有对象
OSS_ALLOWED_PREFIXES = ("covers/", "audio/")


def oss_ready() -> bool:
    return all((OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET, OSS_ENDPOINT))


def oss_host() -> str:
    """资源访问域名，不带结尾斜杠。"""
    host = OSS_ASSET_HOST.strip().rstrip("/")
    if host.startswith("http://"):
        host = "https://" + host[len("http://") :]
    if host:
        return host
    endpoint = OSS_ENDPOINT.replace("https://", "").replace("http://", "").strip("/")
    return f"https://{OSS_BUCKET}.{endpoint}"


def oss_expires_at(ttl: int | None = None) -> int:
    """本次签名的过期时间戳。按 OSS_URL_ALIGN 对齐：同一窗口内签出的地址完全一致。"""
    ttl = OSS_URL_TTL if ttl is None else ttl
    return ((int(time.time()) + ttl) // OSS_URL_ALIGN + 1) * OSS_URL_ALIGN


def sign_oss_url(key: str, ttl: int | None = None) -> str:
    """给私有对象签一个临时 GET 地址（OSS V1：HMAC-SHA1 + Base64 放在 query 上）。"""
    expires = oss_expires_at(ttl)
    string_to_sign = f"GET\n\n\n{expires}\n/{OSS_BUCKET}/{key.lstrip('/')}"
    signature = base64.b64encode(
        hmac.new(
            OSS_ACCESS_KEY_SECRET.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")
    return (
        f"{oss_host()}/{key.lstrip('/')}"
        f"?OSSAccessKeyId={quote(OSS_ACCESS_KEY_ID, safe='')}"
        f"&Expires={expires}&Signature={quote(signature, safe='')}"
    )


def asset_url(path: str, ttl: int | None = None) -> str:
    """库里的 /covers/x.jpg、audio/x.wav 换成私有 Bucket 的签名地址。

    未配置 OSS 时原样返回，本地 /covers 静态目录仍可用，方便回退。
    """
    if not path or path.startswith(("http://", "https://", "data:")):
        return path
    if not oss_ready():
        return path
    return sign_oss_url(path, ttl)

