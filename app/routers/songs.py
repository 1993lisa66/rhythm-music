"""歌曲与歌词（内容类接口：匿名可读，带令牌时附加 liked 状态）。"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_optional_user, user_id_of
from ..models import LyricLine, Song, User
from ..schemas import GenreListOut, LyricsOut, SongListOut, SongOut
from ..services import favorite_ids, get_song, song_out

router = APIRouter(tags=["songs"])


@router.get("/songs", response_model=SongListOut, summary="歌曲列表（搜索 / 筛选 / 排序 / 分页）")
def list_songs(
    q: str | None = Query(None, description="匹配歌名 / 歌手 / 专辑 / 流派"),
    genre: str | None = None,
    liked: bool | None = None,
    sort: Literal["default", "title", "duration", "artist"] = "default",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(50, ge=1, le=200),
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
