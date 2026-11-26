"""注册 / 登录 / 当前账号。

令牌为 HS256 签名的 JWT，放在 Authorization: Bearer <token> 里；
退出登录由客户端丢弃令牌完成（服务端不维护会话），因此 logout 只做确认。
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..deps import get_current_user
from ..errors import bad_request, conflict, unauthorized
from ..models import User
from ..schemas import AccountPatch, LoginIn, OkOut, RegisterIn, TokenOut, UserOut
from ..security import create_token, verify_password
from ..seed import create_user

router = APIRouter(tags=["auth"], prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def user_out(user: User) -> dict:
    return {
        "id": user.public_id,
        "email": user.email,
        "name": user.name,
        "member": user.member,
        "avatar": user.avatar,
    }


def token_payload(user: User) -> dict:
    token, ttl = create_token(user.id)
    return {"token": token, "token_type": "bearer", "expires_in": ttl, "user": user_out(user)}


@router.post("/register", response_model=TokenOut, status_code=201, summary="注册并直接登录")
def register(body: RegisterIn, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise bad_request("邮箱格式不正确", code="invalid_email")
    if len(body.password) < config.PASSWORD_MIN_LENGTH:
        raise bad_request(
            f"密码至少 {config.PASSWORD_MIN_LENGTH} 位", code="password_too_short"
        )
    if db.scalars(select(User).where(User.email == email)).first() is not None:
        raise conflict("该邮箱已注册", code="email_taken")

    user = create_user(db, email=email, password=body.password, name=body.name or "")
    return token_payload(user)


@router.post("/login", response_model=TokenOut, summary="邮箱 + 密码登录")
def login(body: LoginIn, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().lower()
    user = db.scalars(select(User).where(User.email == email)).first()
    # 用户不存在与密码错误返回同一提示，避免暴露邮箱是否已注册
    if user is None or not verify_password(body.password, user.password_hash):
        raise unauthorized("邮箱或密码不正确", code="invalid_credentials")
    return token_payload(user)


@router.get("/me", response_model=UserOut, summary="当前登录账号")
def me(user: User = Depends(get_current_user)) -> dict:
    return user_out(user)


@router.patch("/me", response_model=UserOut, summary="修改昵称 / 头像")
def patch_me(
    body: AccountPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise bad_request("昵称不能为空", code="invalid_name")
        if len(name) > 20:
            raise bad_request("昵称最多 20 个字", code="invalid_name")
        user.name = name
    if body.avatar is not None:
        user.avatar = body.avatar.strip()
    db.commit()
    return user_out(user)


@router.post("/logout", response_model=OkOut, summary="退出登录（客户端丢弃令牌）")
def logout(user: User = Depends(get_current_user)) -> dict:
    return {"ok": True}
