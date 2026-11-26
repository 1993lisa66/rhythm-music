"""初始化数据：把前端 data/*.json 一次性灌进 SQLite。

用法：
    python -m app.seed          # 库为空时才写入（服务启动时也会自动调用）
    python -m app.seed --reset  # 清空并重建
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select

from . import config
from .db import Base, SessionLocal, engine
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
    now_local,
)
from .services import DEFAULT_SETTINGS

# 与前端 store/player.js 的 DEFAULT_QUEUE 保持一致
DEFAULT_QUEUE = [
    "wanfeng",
    "xiaoban",
    "riluo",
    "qinglang",
    "huanghun",
    "xinghe",
    "shanye",
    "chengshiye",
    "manxialai",
    "zaochun",
    "wuye",
    "qingtian",
]

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


def seed(reset: bool = False) -> bool:
    Base.metadata.create_all(engine)

    if reset:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Song)) and not reset:
            return False

        songs = _load("songs") or []
        for order, item in enumerate(songs):
            db.add(
                Song(
                    id=item["id"],
                    title=item["title"],
                    artist=item["artist"],
                    album=item.get("album", ""),
                    genre=item.get("genre", ""),
                    duration=int(item.get("duration", 0)),
                    cover=item.get("cover", ""),
                    added_order=order,
                )
            )
            if item.get("liked"):
                db.add(Favorite(song_id=item["id"]))
        db.flush()

        for order, item in enumerate(_load("playlists") or []):
            db.add(
                Playlist(
                    id=item["id"],
                    title=item["title"],
                    badge=item.get("badge", ""),
                    featured_badge=item.get("featuredBadge"),
                    creator=item.get("creator", ""),
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
                        playlist_id=item["id"],
                        song_id=track["id"],
                        position=pos,
                        duration_override=track.get("duration"),
                    )
                )

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

        for item in (_load("downloads") or {}).get("tracks", []):
            db.add(Download(song_id=item["id"], size=item.get("size", "")))

        recent = _load("recent") or {}
        for group in recent.get("groups", []):
            for index, song_id in enumerate(group.get("songIds", [])):
                db.add(PlayEvent(song_id=song_id, played_at=_seed_time(group.get("label", ""), index)))

        for position, song_id in enumerate(DEFAULT_QUEUE):
            db.add(QueueItem(position=position, song_id=song_id))

        db.add(
            PlayerState(
                id=1,
                index=0,
                position=config.DEFAULT_POSITION,
                playing=False,
                shuffle=False,
                repeat_mode="all",
            )
        )

        for key, value in DEFAULT_SETTINGS.items():
            db.add(Setting(key=key, value=json.dumps(value, ensure_ascii=False)))

        for key in CONTENT_KEYS:
            payload = _load(key)
            if payload is not None:
                db.add(ContentBlock(key=key, payload=json.dumps(payload, ensure_ascii=False)))

        db.commit()
    return True


def ensure_seed() -> None:
    seed(reset=False)


if __name__ == "__main__":
    created = seed(reset="--reset" in sys.argv)
    print("已重建并写入初始数据" if created else "库中已有数据，跳过写入（用 --reset 重建）")
