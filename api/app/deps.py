"""鉴权依赖：从 Authorization: Bearer <token> 解析当前用户。"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .errors import unauthorized
from .models import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False, description="登录后返回的 JWT，格式：Bearer <token>")


def _resolve(
    credentials: HTTPAuthorizationCredentials | None, db: Session
) -> tuple[User | None, str | None]:
    if credentials is None or not credentials.credentials:
        return None, "缺少登录凭证"
    payload = decode_token(credentials.credentials)
    user = db.get(User, payload["sub"])
    if user is None:
        return None, "用户不存在或已注销"
    return user, None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    user, reason = _resolve(credentials, db)
    if user is None:
        raise unauthorized(reason or "请先登录", code="unauthorized")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """内容接口用：带了有效令牌就返回用户（用于 liked 字段），否则匿名。"""
    if credentials is None:
        return None
    user, _ = _resolve(credentials, db)
    return user


def user_id_of(user: User | None) -> str | None:
    return user.id if user is not None else None
