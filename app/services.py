"""业务服务层：序列化、播放器状态机、设置读写。路由层只负责 HTTP 语义。"""

from __future__ import annotations

import json
import random
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from . import config
from .errors import not_found
from .models import (
    ContentBlock,
    Download,
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
    "wifi_only": True,
    "show_lyrics": True,
}


# ---------------------------------------------------------------- 通用
def fmt_time(seconds: int | float) -> str:
    total = max(0, int(seconds or 0))
    return f"{total // 60:02d}:{total % 60:02d}"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def get_song(db: Session, song_id: str) -> Song:
    song = db.get(Song, song_id)
    if song is None:
        raise not_found(f"歌曲不存在：{song_id}", code="song_not_found")
    return song


def get_playlist(db: Session, playlist_id: str) -> Playlist:
    stmt = (
        select(Playlist)
        .options(selectinload(Playlist.tracks).selectinload(PlaylistTrack.song))
        .where(Playlist.id == playlist_id)
    )
    playlist = db.scalars(stmt).first()
    if playlist is None:
        raise not_found(f"歌单不存在：{playlist_id}", code="playlist_not_found")
    return playlist


# ---------------------------------------------------------------- 序列化
def favorite_ids(db: Session) -> set[str]:
    return set(db.scalars(select(Favorite.song_id)).all())


def song_out(song: Song, liked: set[str] | None = None) -> dict:
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "genre": song.genre,
        "duration": song.duration,
        "cover": song.cover,
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
        "cover": playlist.cover,
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


# ---------------------------------------------------------------- 设置
def _read_setting(db: Session, key: str) -> object:
    row = db.get(Setting, key)
    if row is None:
        return DEFAULT_SETTINGS.get(key)
    try:
        return json.loads(row.value)
    except json.JSONDecodeError:
        return DEFAULT_SETTINGS.get(key)


def _write_setting(db: Session, key: str, value: object) -> None:
    row = db.get(Setting, key)
    payload = json.dumps(value, ensure_ascii=False)
    if row is None:
        db.add(Setting(key=key, value=payload))
    else:
        row.value = payload


def settings_payload(db: Session) -> dict:
    return {
        "quality": _read_setting(db, "quality") or "高品质",
        "qualities": list(config.QUALITIES),
        "wifi_only": bool(_read_setting(db, "wifi_only")),
        "show_lyrics": bool(_read_setting(db, "show_lyrics")),
    }


def update_settings(db: Session, **patch: object) -> dict:
    for key, value in patch.items():
        if value is not None:
            _write_setting(db, key, value)
    db.commit()
    return settings_payload(db)


# ---------------------------------------------------------------- 播放队列
def queue_rows(db: Session) -> list[QueueItem]:
    return list(db.scalars(select(QueueItem).order_by(QueueItem.position)).all())


def queue_ids(db: Session) -> list[str]:
    return [row.song_id for row in queue_rows(db)]


def queue_songs(db: Session) -> list[Song]:
    ids = queue_ids(db)
    if not ids:
        return []
    found = {song.id: song for song in db.scalars(select(Song).where(Song.id.in_(ids))).all()}
    return [found[i] for i in ids if i in found]


def set_queue(db: Session, song_ids: list[str], start_index: int = 0, autoplay: bool = True) -> None:
    db.execute(delete(QueueItem))
    for position, song_id in enumerate(song_ids):
        db.add(QueueItem(position=position, song_id=song_id))

    state = get_player(db)
    state.index = max(0, min(start_index, max(len(song_ids) - 1, 0)))
    state.position = 0
    state.playing = autoplay and bool(song_ids)
    db.commit()


# ---------------------------------------------------------------- 播放态
def get_player(db: Session) -> PlayerState:
    state = db.get(PlayerState, 1)
    if state is None:
        state = PlayerState(
            id=1,
            index=0,
            position=config.DEFAULT_POSITION,
            playing=False,
            shuffle=False,
            repeat_mode="all",
        )
        db.add(state)
        db.commit()
    return state


def player_payload(db: Session) -> dict:
    state = get_player(db)
    songs = queue_songs(db)
    liked = favorite_ids(db)

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


def current_duration(db: Session) -> int:
    songs = queue_songs(db)
    if not songs:
        return 0
    state = get_player(db)
    index = int(clamp(state.index, 0, len(songs) - 1))
    return max(songs[index].duration, 1)


def advance_next(db: Session, auto: bool = False) -> dict:
    state = get_player(db)
    ids = queue_ids(db)
    if not ids:
        db.commit()
        return player_payload(db)

    if state.repeat_mode == "one" and auto:
        state.position = 0
        db.commit()
        return player_payload(db)

    if state.shuffle and len(ids) > 1:
        choices = [i for i in range(len(ids)) if i != state.index]
        state.index = random.choice(choices)
    elif state.index >= len(ids) - 1:
        if auto and state.repeat_mode == "off":
            state.position = current_duration(db)
            state.playing = False
            db.commit()
            return player_payload(db)
        state.index = 0
    else:
        state.index += 1

    state.position = 0
    state.playing = True
    db.commit()
    return player_payload(db)


def advance_prev(db: Session) -> dict:
    state = get_player(db)
    ids = queue_ids(db)
    if not ids:
        db.commit()
        return player_payload(db)

    if state.position > 3:
        state.position = 0
        db.commit()
        return player_payload(db)

    state.index = len(ids) - 1 if state.index <= 0 else state.index - 1
    state.position = 0
    state.playing = True
    db.commit()
    return player_payload(db)


def seek_to(db: Session, position: int | None = None, ratio: float | None = None) -> dict:
    state = get_player(db)
    duration = current_duration(db)
    if duration <= 0:
        db.commit()
        return player_payload(db)

    if ratio is not None:
        state.position = int(round(clamp(ratio, 0.0, 1.0) * duration))
    elif position is not None:
        state.position = int(clamp(position, 0, duration))
    db.commit()
    return player_payload(db)


# ---------------------------------------------------------------- 统计
def download_bytes(size_text: str) -> float:
    try:
        return float(str(size_text).split()[0])
    except (ValueError, IndexError):
        return 0.0


def computed_stats(db: Session) -> dict:
    today = now_local().replace(hour=0, minute=0, second=0)
    return {
        "favorites": db.scalar(select(func.count()).select_from(Favorite)) or 0,
        "playlists": db.scalar(select(func.count()).select_from(Playlist)) or 0,
        "songs": db.scalar(select(func.count()).select_from(Song)) or 0,
        "downloads": db.scalar(select(func.count()).select_from(Download)) or 0,
        "today_plays": db.scalar(
            select(func.count()).select_from(PlayEvent).where(PlayEvent.played_at >= today)
        )
        or 0,
        "following": None,
    }


def record_play(db: Session, song_id: str) -> datetime:
    get_song(db, song_id)
    played_at = now_local()
    db.add(PlayEvent(song_id=song_id, played_at=played_at))
    db.commit()
    return played_at


def recent_bucket(played_at: datetime, now: datetime) -> str:
    delta = (now.date() - played_at.date()).days
    if delta <= 0:
        return "今天"
    if delta == 1:
        return "昨天"
    if delta <= 7:
        return "更早"
    return "更早之前"


def recent_groups(db: Session, per_group: int = 20) -> list[dict]:
    """按 今天 / 昨天 / 更早 分组；同一首歌只保留最近一次，避免重复出现。"""
    now = now_local()
    events = db.scalars(select(PlayEvent).order_by(PlayEvent.played_at.desc())).all()
    liked = favorite_ids(db)
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

    order = ["今天", "昨天", "更早", "更早之前"]
    groups = [
        {"label": label, "count": len(buckets[label]), "items": buckets[label]}
        for label in order
        if label in buckets
    ]
    return groups


# ---------------------------------------------------------------- 设置通用读写
def get_setting(db: Session, key: str, default: object = None) -> object:
    value = _read_setting(db, key)
    return default if value is None else value


def set_setting(db: Session, key: str, value: object) -> None:
    _write_setting(db, key, value)
    db.commit()


# ---------------------------------------------------------------- 队列重写
def rewrite_queue(
    db: Session,
    song_ids: list[str],
    index: int,
    position: int,
    playing: bool,
) -> None:
    """整体重写队列并保留播放进度（用于删曲 / 清空）。"""
    db.execute(delete(QueueItem))
    for order, song_id in enumerate(song_ids):
        db.add(QueueItem(position=order, song_id=song_id))

    state = get_player(db)
    state.index = max(0, min(index, max(len(song_ids) - 1, 0)))
    state.position = max(0, position)
    state.playing = playing and bool(song_ids)
    db.commit()
