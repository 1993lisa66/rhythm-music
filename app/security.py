"""密码哈希与 JWT。

刻意只用标准库，避免额外依赖：
- 密码：PBKDF2-HMAC-SHA256 + 每用户随机盐，存储为 pbkdf2_sha256$轮数$盐$哈希
- 令牌：HS256 签名的 JWT（header.payload.signature），密钥来自 RHYTHM_JWT_SECRET
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from . import config
from .errors import unauthorized

PBKDF2_ROUNDS = 260_000
_ALG = "HS256"


# ---------------------------------------------------------------- base64url
def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


# ---------------------------------------------------------------- 密码
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = _b64decode(digest)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _b64decode(salt), int(rounds)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# ---------------------------------------------------------------- JWT
def _sign(message: str) -> str:
    return _b64encode(
        hmac.new(config.JWT_SECRET.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    )


def create_token(user_id: str, ttl: int | None = None) -> tuple[str, int]:
    """返回 (token, 有效期秒数)。"""
    lifetime = ttl if ttl is not None else config.JWT_TTL_SECONDS
    now = int(time.time())
    header = {"alg": _ALG, "typ": "JWT"}
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + lifetime,
        "jti": secrets.token_urlsafe(8),
    }
    segments = [
        _b64encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments)
    return f"{signing_input}.{_sign(signing_input)}", lifetime


def decode_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise unauthorized("登录凭证格式不正确", code="invalid_token")

    signing_input = f"{parts[0]}.{parts[1]}"
    if not hmac.compare_digest(_sign(signing_input), parts[2]):
        raise unauthorized("登录凭证校验失败", code="invalid_token")

    try:
        payload = json.loads(_b64decode(parts[1]))
    except (ValueError, json.JSONDecodeError):
        raise unauthorized("登录凭证无法解析", code="invalid_token") from None

    if not isinstance(payload.get("sub"), str) or not payload["sub"]:
        raise unauthorized("登录凭证内容异常", code="invalid_token")
    if int(payload.get("exp", 0)) <= int(time.time()):
        raise unauthorized("登录已过期，请重新登录", code="token_expired")
    return payload
