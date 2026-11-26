"""歌曲与歌词（内容类接口：匿名可读，带令牌时附加 liked 状态）。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user, user_id_of
from ..errors import ApiError, not_found
from ..lyrics_source import fetch_lyrics
from ..models import (
    Download,
    Favorite,
    LyricLine,
    PlayEvent,
    PlaylistTrack,
    QueueItem,
    Song,
    User,
)
from ..schemas import GenreListOut, LyricsOut, SongDeleteOut, SongListOut, SongOut
from ..services import (
    clamp,
    delete_oss_object,
    favorite_ids,
    get_player,
    get_song,
    oss_object_key,
    queue_ids,
    rewrite_queue,
    song_out,
)

router = APIRouter(tags=["songs"])


@router.get("/songs", response_model=SongListOut, summary="歌曲列表（搜索 / 筛选 / 排序 / 分页）")
def list_songs(
    q: str | None = Query(None, description="匹配歌名 / 歌手 / 专辑 / 流派"),
    genre: str | None = None,
    liked: bool | None = None,
    sort: Literal["default", "title", "duration", "artist"] = "default",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(50, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Song)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Song.title.like(like),
                Song.artist.like(like),
                Song.album.like(like),
                Song.genre.like(like),
            )
        )
    if genre:
        stmt = stmt.where(Song.genre == genre)

    liked_ids = favorite_ids(db, user_id_of(user))
    if liked is True:
        if not liked_ids:
            return {"total": 0, "items": []}
        stmt = stmt.where(Song.id.in_(liked_ids))
    elif liked is False and liked_ids:
        stmt = stmt.where(Song.id.notin_(liked_ids))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    column = {"title": Song.title, "duration": Song.duration, "artist": Song.artist}.get(sort)
    if column is not None:
        stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())
    else:
        stmt = stmt.order_by(Song.added_order.asc())

    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return {"total": total, "items": [song_out(song, liked_ids) for song in rows]}


@router.get("/genres", response_model=GenreListOut, summary="全部流派及曲目数")
def list_genres(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(Song.genre, func.count()).group_by(Song.genre).order_by(func.count().desc())
    ).all()
    return {"items": [{"name": name, "count": count} for name, count in rows]}


@router.get("/songs/{song_id}", response_model=SongOut, summary="单曲详情")
def get_song_detail(
    song_id: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    song = get_song(db, song_id)
    return song_out(song, favorite_ids(db, user_id_of(user)))


@router.delete("/songs/{song_id}", response_model=SongDeleteOut, summary="删除歌曲及其资源")
def delete_song(
    song_id: str,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """从曲库彻底删除一首歌。

    先清掉关联数据（歌单曲目 / 收藏 / 播放记录 / 下载 / 队列 / 歌词），
    再删 OSS 上的音频与封面对象。资源删除是 best-effort：
    OSS 未配置或请求失败不会回滚曲库记录的移除。
    """
    song = get_song(db, song_id)
    keys = [key for key in (oss_object_key(song.audio), oss_object_key(song.cover)) if key]

    db.execute(delete(LyricLine).where(LyricLine.song_id == song_id))
    db.execute(delete(PlaylistTrack).where(PlaylistTrack.song_id == song_id))
    db.execute(delete(Favorite).where(Favorite.song_id == song_id))
    db.execute(delete(PlayEvent).where(PlayEvent.song_id == song_id))
    db.execute(delete(Download).where(Download.song_id == song_id))

    # 用户队列里可能还排着这首歌：逐用户重写队列并修正当前下标
    affected = db.scalars(
        select(QueueItem.user_id).where(QueueItem.song_id == song_id).distinct()
    ).all()
    for user_id in affected:
        state = get_player(db, user_id)
        ids = queue_ids(db, user_id)
        if song_id not in ids:
            continue
        old_index = int(clamp(state.index, 0, max(len(ids) - 1, 0)))
        was_current = ids[old_index] == song_id
        removed_before = sum(1 for sid in ids[:old_index] if sid == song_id)
        remaining = [sid for sid in ids if sid != song_id]
        new_index = 0 if was_current else max(0, old_index - removed_before)
        rewrite_queue(
            db,
            user_id,
            remaining,
            new_index,
            0 if was_current else state.position,
            state.playing,
        )

    db.delete(song)
    db.commit()

    assets_removed = sum(1 for key in keys if delete_oss_object(key))
    return {"deleted": True, "song_id": song_id, "assets_removed": assets_removed}


@router.get("/songs/{song_id}/lyrics", response_model=LyricsOut, summary="歌词（时间轴）")
def get_lyrics(song_id: str, db: Session = Depends(get_db)) -> dict:
    song = get_song(db, song_id)
    lines = db.scalars(
        select(LyricLine).where(LyricLine.song_id == song_id).order_by(LyricLine.position)
    ).all()
    return {
        "song_id": song.id,
        "title": song.title,
        "has_lyrics": bool(lines),
        "lines": [{"t": line.t, "text": line.text} for line in lines],
    }


@router.post(
    "/songs/{song_id}/lyrics/fetch",
    response_model=LyricsOut,
    summary="在线查找歌词并保存到曲库",
)
def fetch_song_lyrics(song_id: str, db: Session = Depends(get_db)) -> dict:
    """从 LRCLIB 按歌名 / 歌手 / 时长精确匹配，命中后覆盖本地歌词。

    未收录返回 404；歌词服务不可达返回 502。找不到时不会写入任何猜测内容。
    """
    song = get_song(db, song_id)
    try:
        lines = fetch_lyrics(song.title, song.artist, song.duration)
    except RuntimeError as error:
        raise ApiError(502, "lyrics_source_error", str(error)) from error
    if not lines:
        raise not_found("歌词库暂未收录这首歌", code="lyrics_not_found")

    db.execute(delete(LyricLine).where(LyricLine.song_id == song_id))
    db.add_all(
        [
            LyricLine(song_id=song_id, position=index, t=item["t"], text=item["text"])
            for index, item in enumerate(lines)
        ]
    )
    db.commit()
    return {
        "song_id": song_id,
        "title": song.title,
        "has_lyrics": True,
        "lines": lines,
    }
