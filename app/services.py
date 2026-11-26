"""业务服务层：序列化、播放器状态机、设置读写。

所有涉及用户状态（收藏 / 播放记录 / 下载 / 队列 / 播放态 / 设置）的函数都要求显式传入
user_id，路由层通过鉴权依赖拿到当前用户后透传，避免出现跨用户读写。
"""

from __future__ import annotations

import json
import random
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from . import config
from .errors import not_found
from .models import (
    ContentBlock,
    Favorite,
    PlayEvent,
    PlayerState,
    Playlist,
    PlaylistTrack,
    QueueItem,
    Setting,
    Song,
    now_local,
)

DEFAULT_SETTINGS: dict[str, object] = {
    "quality": "高品质",
    "show_lyrics": True,
}


# ---------------------------------------------------------------- 通用
def fmt_time(seconds: int | float) -> str:
    total = max(0, int(seconds or 0))
    return f"{total // 60:02d}:{total % 60:02d}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def oss_object_key(value: str) -> str:
    """把对象键或完整 URL 归一成 OSS 对象键（与 assets 换签同口径）。"""
    text = (value or "").strip()
    if not text:
        return ""
    if text.startswith("//"):
        text = "https:" + text
    if text.startswith(("http://", "https://")):
        text = urlparse(text).path
    return text.split("?")[0].split("#")[0].lstrip("/")


def delete_oss_object(key: str) -> bool:
    """删除 OSS 上的单个对象。

    未配置 OSS、键为空或请求失败都返回 False，不抛异常：
    资源清理是 best-effort，不能因为删文件失败而回滚曲库记录的删除。
    """
    if not key or not config.oss_ready():
        return False
    try:
        request = urllib.request.Request(config.delete_oss_url(key), method="DELETE")
        with urllib.request.urlopen(request, timeout=8) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, OSError, ValueError):
        return False


def get_song(db: Session, song_id: str) -> Song:
    song = db.get(Song, song_id)
    if song is None:
        raise not_found(f"歌曲不存在：{song_id}", code="song_not_found")
    return song


def get_user_playlist(db: Session, user_id: str, playlist_id: str) -> Playlist:
    stmt = (
        select(Playlist)
        .options(selectinload(Playlist.tracks).selectinload(PlaylistTrack.song))
        .where(
            Playlist.id == playlist_id,
            or_(Playlist.owner_id == user_id, Playlist.owner_id.is_(None)),
        )
    )
    playlist = db.scalars(stmt).first()
    if playlist is None:
        raise not_found(f"歌单不存在：{playlist_id}", code="playlist_not_found")
    return playlist


# ---------------------------------------------------------------- 序列化
def favorite_ids(db: Session, user_id: str | None) -> set[str]:
    if not user_id:
        return set()
    return set(
        db.scalars(select(Favorite.song_id).where(Favorite.user_id == user_id)).all()
    )


def song_out(song: Song, liked: set[str] | None = None) -> dict:
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "genre": song.genre,
        "duration": song.duration,
        "cover": config.asset_url(song.cover),
        "audio": config.asset_url(song.audio),
        "liked": song.id in liked if liked is not None else False,
    }


def playlist_summary(playlist: Playlist, track_count: int | None = None) -> dict:
    count = track_count if track_count is not None else len(playlist.tracks)
    return {
        "id": playlist.id,
        "title": playlist.title,
        "badge": playlist.badge,
        "featured_badge": playlist.featured_badge,
        "creator": playlist.creator,
        "count": playlist.total_count or count,
        "track_count": count,
        "duration_text": playlist.duration_text,
        "desc": playlist.desc,
        "info": playlist.info,
        "cover": config.asset_url(playlist.cover),
        "tone": playlist.tone,
    }


def playlist_detail(playlist: Playlist, liked: set[str] | None = None) -> dict:
    tracks = []
    for i, item in enumerate(playlist.tracks):
        if item.song is None:
            continue
        row = song_out(item.song, liked)
        row["duration"] = item.duration_override or item.song.duration
        row["index"] = i
        tracks.append(row)
    payload = playlist_summary(playlist, len(tracks))
    payload["tracks"] = tracks
    return payload


# ---------------------------------------------------------------- 文案块
def get_content(db: Session, key: str) -> dict:
    block = db.get(ContentBlock, key)
    if block is None:
        return {}
    try:
        return json.loads(block.payload)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------- 设置（按用户）
def _read_setting(db: Session, user_id: str, key: str) -> object:
    row = db.get(Setting, (user_id, key))
    if row is None:
        return DEFAULT_SETTINGS.get(key)
    try:
        return json.loads(row.value)
    except json.JSONDecodeError:
        return DEFAULT_SETTINGS.get(key)


def _write_setting(db: Session, user_id: str, key: str, value: object) -> None:
    row = db.get(Setting, (user_id, key))
    payload = json.dumps(value, ensure_ascii=False)
    if row is None:
        db.add(Setting(user_id=user_id, key=key, value=payload))
    else:
        row.value = payload


def settings_payload(db: Session, user_id: str) -> dict:
    return {
        "quality": _read_setting(db, user_id, "quality") or "高品质",
        "qualities": list(config.QUALITIES),
        "show_lyrics": bool(_read_setting(db, user_id, "show_lyrics")),
    }


def update_settings(db: Session, user_id: str, **patch: object) -> dict:
    for key, value in patch.items():
        if value is not None:
            _write_setting(db, user_id, key, value)
    db.commit()
    return settings_payload(db, user_id)


# ---------------------------------------------------------------- 播放队列（按用户）
def queue_rows(db: Session, user_id: str) -> list[QueueItem]:
    return list(
        db.scalars(
            select(QueueItem)
            .where(QueueItem.user_id == user_id)
            .order_by(QueueItem.position)
        ).all()
    )


def queue_ids(db: Session, user_id: str) -> list[str]:
    return [row.song_id for row in queue_rows(db, user_id)]


def queue_songs(db: Session, user_id: str) -> list[Song]:
    ids = queue_ids(db, user_id)
    if not ids:
        return []
    found = {song.id: song for song in db.scalars(select(Song).where(Song.id.in_(ids))).all()}
    return [found[i] for i in ids if i in found]


def set_queue(
    db: Session,
    user_id: str,
    song_ids: list[str],
    start_index: int = 0,
    autoplay: bool = True,
) -> None:
    db.execute(delete(QueueItem).where(QueueItem.user_id == user_id))
    for position, song_id in enumerate(song_ids):
        db.add(QueueItem(user_id=user_id, position=position, song_id=song_id))

    state = get_player(db, user_id)
    state.index = max(0, min(start_index, max(len(song_ids) - 1, 0)))
    state.position = 0
    state.playing = autoplay and bool(song_ids)
    db.commit()


# ---------------------------------------------------------------- 播放态（按用户）
def get_player(db: Session, user_id: str) -> PlayerState:
    state = db.get(PlayerState, user_id)
    if state is None:
        state = PlayerState(
            user_id=user_id,
            index=0,
            position=config.DEFAULT_POSITION,
            playing=False,
            shuffle=False,
            repeat_mode="all",
        )
        db.add(state)
        db.commit()
    return state


def player_payload(db: Session, user_id: str) -> dict:
    state = get_player(db, user_id)
    songs = queue_songs(db, user_id)
    liked = favorite_ids(db, user_id)

    if not songs:
        return {
            "playing": False,
            "shuffle": state.shuffle,
            "repeat": state.repeat_mode,
            "index": 0,
            "position": 0,
            "position_text": fmt_time(0),
            "duration": 0,
            "duration_text": fmt_time(0),
            "progress": 0.0,
            "current": None,
            "queue": [],
            "liked": False,
        }

    index = int(clamp(state.index, 0, len(songs) - 1))
    current = songs[index]
    duration = max(current.duration, 1)
    position = int(clamp(state.position, 0, duration))

    return {
        "playing": bool(state.playing),
        "shuffle": bool(state.shuffle),
        "repeat": state.repeat_mode,
        "index": index,
        "position": position,
        "position_text": fmt_time(position),
        "duration": duration,
        "duration_text": fmt_time(duration),
        "progress": round(min(position / duration, 1.0), 4),
        "current": song_out(current, liked),
        "queue": [song_out(song, liked) for song in songs],
        "liked": current.id in liked,
    }


def current_duration(db: Session, user_id: str) -> int:
    songs = queue_songs(db, user_id)
    if not songs:
        return 0
    state = get_player(db, user_id)
    index = int(clamp(state.index, 0, len(songs) - 1))
    return max(songs[index].duration, 1)


def advance_next(db: Session, user_id: str, auto: bool = False) -> dict:
    state = get_player(db, user_id)
    ids = queue_ids(db, user_id)
    if not ids:
        db.commit()
        return player_payload(db, user_id)

    if state.repeat_mode == "one" and auto:
        state.position = 0
        db.commit()
        return player_payload(db, user_id)

    if state.shuffle and len(ids) > 1:
        choices = [i for i in range(len(ids)) if i != state.index]
        state.index = random.choice(choices)
    elif state.index >= len(ids) - 1:
        if auto and state.repeat_mode == "off":
            state.position = current_duration(db, user_id)
            state.playing = False
            db.commit()
            return player_payload(db, user_id)
        state.index = 0
    else:
        state.index += 1

    state.position = 0
    state.playing = True
    db.commit()
    return player_payload(db, user_id)


def advance_prev(db: Session, user_id: str) -> dict:
    state = get_player(db, user_id)
    ids = queue_ids(db, user_id)
    if not ids:
        db.commit()
        return player_payload(db, user_id)

    if state.position > 3:
        state.position = 0
        db.commit()
        return player_payload(db, user_id)

    state.index = len(ids) - 1 if state.index <= 0 else state.index - 1
    state.position = 0
    state.playing = True
    db.commit()
    return player_payload(db, user_id)


def seek_to(
    db: Session,
    user_id: str,
    position: int | None = None,
    ratio: float | None = None,
) -> dict:
    state = get_player(db, user_id)
    duration = current_duration(db, user_id)
    if duration <= 0:
        db.commit()
        return player_payload(db, user_id)

    if ratio is not None:
        state.position = int(round(clamp(ratio, 0.0, 1.0) * duration))
    elif position is not None:
        state.position = int(clamp(position, 0, duration))
    db.commit()
    return player_payload(db, user_id)


def rewrite_queue(
    db: Session,
    user_id: str,
    song_ids: list[str],
    index: int,
    position: int,
    playing: bool,
) -> None:
    """整体重写队列并保留播放进度（用于删曲 / 清空 / 追加）。"""
    db.execute(delete(QueueItem).where(QueueItem.user_id == user_id))
    for order, song_id in enumerate(song_ids):
        db.add(QueueItem(user_id=user_id, position=order, song_id=song_id))

    state = get_player(db, user_id)
    state.index = max(0, min(index, max(len(song_ids) - 1, 0)))
    state.position = max(0, position)
    state.playing = playing and bool(song_ids)
    db.commit()


# ---------------------------------------------------------------- 统计（按用户）
def computed_stats(db: Session, user_id: str) -> dict:
    today = now_local().replace(hour=0, minute=0, second=0)
    return {
        "favorites": db.scalar(
            select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
        )
        or 0,
        "playlists": db.scalar(
            select(func.count()).select_from(Playlist).where(Playlist.owner_id == user_id)
        )
        or 0,
        "songs": db.scalar(select(func.count()).select_from(Song)) or 0,
        "today_plays": db.scalar(
            select(func.count())
            .select_from(PlayEvent)
            .where(PlayEvent.user_id == user_id, PlayEvent.played_at >= today)
        )
        or 0,
        "following": None,
    }


def record_play(db: Session, user_id: str, song_id: str) -> datetime:
    get_song(db, song_id)
    played_at = now_local()
    db.add(PlayEvent(user_id=user_id, song_id=song_id, played_at=played_at))
    db.commit()
    return played_at


def recent_bucket(played_at: datetime, now: datetime) -> str:
    delta = (now.date() - played_at.date()).days
    if delta <= 0:
        return "今天"
    if delta == 1:
        return "昨天"
    return "更早"


def recent_groups(db: Session, user_id: str, per_group: int = 20) -> list[dict]:
    """按 今天 / 昨天 / 更早 分组；同一首歌只保留最近一次，避免重复出现。"""
    now = now_local()
    events = db.scalars(
        select(PlayEvent)
        .where(PlayEvent.user_id == user_id)
        .order_by(PlayEvent.played_at.desc())
    ).all()
    liked = favorite_ids(db, user_id)
    seen: set[str] = set()
    buckets: dict[str, list[dict]] = {}

    for event in events:
        if event.song_id in seen:
            continue
        song = db.get(Song, event.song_id)
        if song is None:
            continue
        seen.add(event.song_id)
        label = recent_bucket(event.played_at, now)
        row = song_out(song, liked)
        row["played_at"] = event.played_at
        buckets.setdefault(label, [])
        if len(buckets[label]) < per_group:
            buckets[label].append(row)

    order = ["今天", "昨天", "更早"]
    return [
        {"label": label, "count": len(buckets[label]), "items": buckets[label]}
        for label in order
        if label in buckets
    ]


# ---------------------------------------------------------------- 设置通用读写（按用户）
def get_setting(db: Session, user_id: str | None, key: str, default: object = None) -> object:
    if not user_id:
        return default
    value = _read_setting(db, user_id, key)
    return default if value is None else value


def set_setting(db: Session, user_id: str | None, key: str, value: object) -> None:
    if not user_id:
        return
    _write_setting(db, user_id, key, value)
    db.commit()
