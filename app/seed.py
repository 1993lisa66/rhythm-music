"""初始化数据。

分层：
1. 内容层（全用户共享）：歌曲、歌词、首页/乐库/我的/搜索的固定文案；
2. 用户层（注册时按需生成）：播放态、初始队列、默认设置、4 个初始歌单；
3. 演示账号：拥有设计稿里的收藏 / 最近播放 / 离线下载数据，便于对照验收。

用法：
    python -m app.seed          # 内容为空时写入，并确保演示账号存在
    python -m app.seed --reset  # 删库重建
"""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import config
from .db import Base, SessionLocal, engine, ensure_columns
from .models import (
    ContentBlock,
    Download,
    Favorite,
    LyricLine,
    PlayEvent,
    PlayerState,
    Playlist,
    PlaylistTrack,
    QueueItem,
    Setting,
    Song,
    User,
    now_local,
)
from .security import hash_password
from .services import DEFAULT_SETTINGS

# 初始队列取曲库前 12 首（对象键写在 songs.json 里，避免换库后残留旧 id）
def default_queue() -> list[str]:
    return [item["id"] for item in (_load("songs") or [])[:12]]

CONTENT_KEYS = ("discover", "library", "profile", "search")


def _load(name: str) -> object:
    path: Path = config.SEED_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _seed_time(label: str, index: int):
    now = now_local()
    today_start = now.replace(hour=0, minute=0, second=0)
    if label == "今天":
        return now - timedelta(minutes=16 + index * 21)
    if label == "昨天":
        return today_start - timedelta(minutes=38 + index * 33)
    return today_start - timedelta(days=3, minutes=12 + index * 47)


# ---------------------------------------------------------------- 内容层
def seed_content(db: Session) -> None:
    for order, item in enumerate(_load("songs") or []):
        db.add(
            Song(
                id=item["id"],
                title=item["title"],
                artist=item["artist"],
                album=item.get("album", ""),
                genre=item.get("genre", ""),
                duration=int(item.get("duration", 0)),
                cover=item.get("cover", ""),
                audio=item.get("audio", ""),
                added_order=order,
            )
        )
    # 外键已开启，先落盘歌曲再写歌词，否则歌词的 song_id 找不到父行
    db.flush()

    for song_id, payload in (_load("lyrics") or {}).items():
        for pos, line in enumerate(payload.get("lines", [])):
            db.add(
                LyricLine(
                    song_id=song_id,
                    position=pos,
                    t=int(line.get("t", 0)),
                    text=line.get("text", ""),
                )
            )

    for key in CONTENT_KEYS:
        payload = _load(key)
        if payload is not None:
            db.add(ContentBlock(key=key, payload=json.dumps(payload, ensure_ascii=False)))

    db.commit()


# ---------------------------------------------------------------- 用户层
def _next_user_number(db: Session) -> int:
    """分配一个 8 位展示编号（对应设计稿的 “ID: 8823 6102”），冲突则重试。"""
    for _ in range(50):
        candidate = random.randint(10_000_000, 99_999_999)
        if db.scalar(select(User.id).where(User.number == candidate)) is None:
            return candidate
    raise RuntimeError("无法分配用户编号，请检查 users 表")


def provision_user(db: Session, user: User, with_demo_data: bool = False) -> None:
    """为新用户生成初始队列、播放态、默认设置与 4 个初始歌单。"""
    if db.get(PlayerState, user.id) is None:
        db.add(
            PlayerState(
                user_id=user.id,
                index=0,
                position=config.DEFAULT_POSITION if with_demo_data else 0,
                playing=False,
                shuffle=False,
                repeat_mode="all",
            )
        )

    if not user.avatar:
        user.avatar = "/covers/avatar.jpg"

    if not db.scalar(select(QueueItem.position).where(QueueItem.user_id == user.id)):
        for position, song_id in enumerate(default_queue()):
            db.add(QueueItem(user_id=user.id, position=position, song_id=song_id))

    for key, value in DEFAULT_SETTINGS.items():
        if db.get(Setting, (user.id, key)) is None:
            db.add(Setting(user_id=user.id, key=key, value=json.dumps(value, ensure_ascii=False)))

    for order, item in enumerate(_load("playlists") or []):
        playlist_id = f"{user.id}-{item['id']}"
        if db.get(Playlist, playlist_id) is not None:
            continue
        db.add(
            Playlist(
                id=playlist_id,
                owner_id=user.id,
                title=item["title"],
                badge=item.get("badge", ""),
                featured_badge=item.get("featuredBadge"),
                creator=user.name,
                total_count=int(item.get("count", 0)),
                duration_text=item.get("durationText", ""),
                desc=item.get("desc", ""),
                info=item.get("info", ""),
                cover=item.get("cover", ""),
                tone=item.get("tone", "sunset"),
                position=order,
            )
        )
        db.flush()
        for pos, track in enumerate(item.get("tracks", [])):
            db.add(
                PlaylistTrack(
                    playlist_id=playlist_id,
                    song_id=track["id"],
                    position=pos,
                    duration_override=track.get("duration"),
                )
            )

    if with_demo_data:
        for item in _load("songs") or []:
            if item.get("liked"):
                db.add(Favorite(user_id=user.id, song_id=item["id"]))

        for item in (_load("downloads") or {}).get("tracks", []):
            db.add(Download(user_id=user.id, song_id=item["id"], size=item.get("size", "")))

        recent = _load("recent") or {}
        for group in recent.get("groups", []):
            for index, song_id in enumerate(group.get("songIds", [])):
                db.add(
                    PlayEvent(
                        user_id=user.id,
                        song_id=song_id,
                        played_at=_seed_time(group.get("label", ""), index),
                    )
                )

    db.commit()


def create_user(
    db: Session,
    email: str,
    password: str,
    name: str = "",
    with_demo_data: bool = False,
) -> User:
    user = User(
        id=uuid.uuid4().hex[:12],
        number=_next_user_number(db),
        email=email.strip().lower(),
        name=name.strip() or email.split("@")[0],
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()
    provision_user(db, user, with_demo_data=with_demo_data)
    db.commit()
    return user


# ---------------------------------------------------------------- 入口
def sync_audio_keys(db: Session) -> int:
    """把 songs.json 里的 audio 字段同步到已有库。

    音频对象键放在内容文件里，是唯一来源；这里只补写入库后新增的键，
    不改歌名/时长等其他字段，避免覆盖人工调整。
    """
    updated = 0
    for item in _load("songs") or []:
        audio = item.get("audio", "")
        if not audio:
            continue
        song = db.get(Song, item["id"])
        if song is not None and song.audio != audio:
            song.audio = audio
            updated += 1
    if updated:
        db.commit()
    return updated


def seed(reset: bool = False) -> bool:
    Base.metadata.create_all(engine)
    ensure_columns()

    if reset:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    with SessionLocal() as db:
        created = not db.scalar(select(func.count()).select_from(Song))
        if created:
            seed_content(db)
        else:
            sync_audio_keys(db)

        demo = db.scalars(select(User).where(User.email == config.DEMO_EMAIL.lower())).first()
        if demo is None:
            create_user(
                db,
                email=config.DEMO_EMAIL,
                password=config.DEMO_PASSWORD,
                name=config.DEMO_NAME,
                with_demo_data=True,
            )
            created = True
        return created


def ensure_seed() -> None:
    seed(reset=False)


if __name__ == "__main__":
    built = seed(reset="--reset" in sys.argv)
    print("已重建并写入初始数据" if built else "数据已存在，跳过写入（用 --reset 重建）")
    print(f"演示账号：{config.DEMO_EMAIL} / {config.DEMO_PASSWORD}")
