"""资源换签：私有 Bucket 的地址有有效期，前端在到期前用这个接口换一批新地址。

页面开着超过 OSS_URL_TTL 后，旧地址会 403；换签只重算签名，不搬文件。
入参既可以是对象键（covers/cover_1.jpg），也可以是旧的签名地址，
前端把当前在用的地址原样丢回来即可。
"""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends

from .. import config
from ..deps import get_optional_user
from ..schemas import SignIn, SignOut

router = APIRouter(prefix="/assets", tags=["assets"])

# 一次最多换 100 个，避免被当成批量探测工具
MAX_PATHS = 100


def _object_key(value: str) -> str:
    """把对象键或完整 URL 归一成 OSS 对象键。"""
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    if value.startswith(("http://", "https://")):
        value = urlparse(value).path
    return value.split("?")[0].split("#")[0].lstrip("/")


@router.post("/sign", response_model=SignOut, summary="换签资源地址")
def sign_assets(payload: SignIn, _user=Depends(get_optional_user)) -> dict:
    """返回这批对象的新签名地址与统一过期时间；不在白名单前缀下的键会被忽略。"""
    keys: list[str] = []
    for path in payload.paths[:MAX_PATHS]:
        key = _object_key(path)
        if key and key.startswith(config.OSS_ALLOWED_PREFIXES) and key not in keys:
            keys.append(key)

    expires_at = config.oss_expires_at()
    return {
        "items": [
            {
                "key": key,
                "url": config.sign_oss_url(key),
                "expires_at": expires_at,
            }
            for key in keys
        ],
        "expires_at": expires_at,
        "ttl": config.OSS_URL_TTL,
    }
