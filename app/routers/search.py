"""搜索：结果聚合、热搜词与「换一换」、输入联想。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Playlist, Song
from ..schemas import HotOut, SearchOut, SuggestOut
from ..services import (
    favorite_ids,
    get_content,
    get_setting,
    playlist_summary,
    set_setting,
    song_out,
)

router = APIRouter(tags=["search"])

TONES = ["primary", "sage", "honey", "plum"]
HOT_SIZE = 4


def _hot_pool(db: Session) -> list[str]:
    """热搜池：设计稿的 4 个词 + 曲库流派 + 歌手，保证「换一换」有词可换。"""
    content = get_content(db, "search")
    words = [item.get("text", "") for item in content.get("hot", {}).get("items", [])]
    words += list(db.scalars(select(Song.genre).distinct().order_by(Song.genre)).all())
    words += list(db.scalars(select(Song.artist).distinct().order_by(Song.artist)).all())

    deduped: list[str] = []
    for word in words:
        if word and word not in deduped:
            deduped.append(word)
    return deduped


def _hot_items(db: Session, offset: int) -> list[dict]:
    pool = _hot_pool(db)
    if not pool:
        return []
    start = offset % len(pool)
    rotated = pool[start:] + pool[:start]
    return [
        {"text": word, "tone": TONES[index % len(TONES)]}
        for index, word in enumerate(rotated[:HOT_SIZE])
    ]


@router.get("/search", response_model=SearchOut, summary="搜索歌曲 / 歌单 / 歌手")
def search(
    q: str = Query(..., min_length=1, description="关键字，匹配歌名 / 歌手 / 专辑 / 流派 / 歌单标题"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    keyword = q.strip()
    like = f"%{keyword}%"
    liked = favorite_ids(db)

    song_rows = db.scalars(
        select(Song)
        .where(
            or_(
                Song.title.like(like),
                Song.artist.like(like),
                Song.album.like(like),
                Song.genre.like(like),
            )
        )
        .order_by(Song.added_order)
        .limit(limit)
    ).all()

    playlist_rows = db.scalars(
        select(Playlist)
        .where(or_(Playlist.title.like(like), Playlist.desc.like(like), Playlist.badge.like(like)))
        .order_by(Playlist.position)
        .limit(limit)
    ).all()

    artist_rows = db.execute(
        select(Song.artist, func.count(), func.min(Song.cover))
        .where(Song.artist.like(like))
        .group_by(Song.artist)
        .limit(limit)
    ).all()

    songs = [song_out(song, liked) for song in song_rows]
    playlists = [playlist_summary(item) for item in playlist_rows]
    artists = [
        {"name": name, "song_count": count, "cover": cover or ""}
        for name, count, cover in artist_rows
    ]

    return {
        "query": keyword,
        "total": len(songs) + len(playlists) + len(artists),
        "songs": songs,
        "playlists": playlists,
        "artists": artists,
    }


@router.get("/search/hot", response_model=HotOut, summary="热门搜索词")
def hot(db: Session = Depends(get_db)) -> dict:
    content = get_content(db, "search")
    copy = content.get("hot", {})
    offset = int(get_setting(db, "hot_offset", 0) or 0)
    return {
        "title": copy.get("title", "热门搜索"),
        "refresh": copy.get("refresh", "换一换"),
        "items": _hot_items(db, offset),
    }


@router.post("/search/hot/refresh", response_model=HotOut, summary="换一换")
def refresh_hot(db: Session = Depends(get_db)) -> dict:
    content = get_content(db, "search")
    copy = content.get("hot", {})
    pool_size = max(len(_hot_pool(db)), 1)
    offset = int(get_setting(db, "hot_offset", 0) or 0)
    offset = (offset + HOT_SIZE) % pool_size
    set_setting(db, "hot_offset", offset)
    return {
        "title": copy.get("title", "热门搜索"),
        "refresh": copy.get("refresh", "换一换"),
        "items": _hot_items(db, offset),
    }


@router.get("/search/suggest", response_model=SuggestOut, summary="输入联想")
def suggest(
    q: str = Query("", description="已输入内容"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> dict:
    keyword = q.strip()
    if not keyword:
        return {"query": "", "items": []}

    like = f"%{keyword}%"
    titles = list(
        db.scalars(select(Song.title).where(Song.title.like(like)).limit(limit)).all()
    )
    artists = list(
        db.scalars(select(Song.artist).distinct().where(Song.artist.like(like)).limit(limit)).all()
    )
    items: list[str] = []
    for word in titles + artists:
        if word not in items:
            items.append(word)
    return {"query": keyword, "items": items[:limit]}
