"""聚合页：发现首页、音乐库（含专辑视图）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Playlist, Song
from ..schemas import AlbumListOut, DiscoverOut, LibraryOut
from ..services import (
    favorite_ids,
    get_content,
    playlist_summary,
    song_out,
)

router = APIRouter(tags=["browse"])


def _songs_by_ids(db: Session, ids: list[str], liked: set[str]) -> list[dict]:
    if not ids:
        return []
    found = {song.id: song for song in db.scalars(select(Song).where(Song.id.in_(ids))).all()}
    return [song_out(found[i], liked) for i in ids if i in found]


def _playlist_map(db: Session, ids: list[str]) -> dict[str, Playlist]:
    if not ids:
        return {}
    rows = db.scalars(select(Playlist).where(Playlist.id.in_(ids))).all()
    return {row.id: row for row in rows}


@router.get("/discover", response_model=DiscoverOut, summary="发现首页聚合")
def get_discover(db: Session = Depends(get_db)) -> dict:
    content = get_content(db, "discover")
    liked = favorite_ids(db)

    featured_copy = content.get("featured", {})
    featured_playlist = None
    playlist_id = featured_copy.get("playlistId")
    if playlist_id:
        playlist = db.get(Playlist, playlist_id)
        if playlist is not None:
            featured_playlist = playlist_summary(playlist)

    recent_copy = content.get("recent", {})
    moods_copy = content.get("moods", {})

    return {
        "greeting": content.get("greeting", ""),
        "headline": content.get("headline", ""),
        "search_placeholder": content.get("searchPlaceholder", ""),
        "featured": {
            "section_title": featured_copy.get("sectionTitle", "今日推荐"),
            "more": featured_copy.get("more", "全部 ›"),
            "playlist": featured_playlist,
        },
        "moods": {
            "title": moods_copy.get("title", "随心听"),
            "items": moods_copy.get("items", []),
        },
        "recent": {
            "title": recent_copy.get("title", "最近播放"),
            "more": recent_copy.get("more", "全部 ›"),
            "items": _songs_by_ids(db, recent_copy.get("songIds", []), liked),
        },
    }


@router.get("/library", response_model=LibraryOut, summary="音乐库聚合")
def get_library(db: Session = Depends(get_db)) -> dict:
    content = get_content(db, "library")
    liked = favorite_ids(db)

    recent_copy = content.get("recent", {})
    playlists_copy = content.get("playlists", {})
    playlist_ids = playlists_copy.get("ids", [])
    playlists = _playlist_map(db, playlist_ids)

    return {
        "title": content.get("title", "音乐库"),
        "search_placeholder": content.get("searchPlaceholder", "搜索我的音乐"),
        "tabs": content.get("tabs", ["歌曲", "歌单", "专辑"]),
        "recent": {
            "title": recent_copy.get("title", "最近添加"),
            "more": recent_copy.get("more", "全部 ›"),
            "items": _songs_by_ids(db, recent_copy.get("songIds", []), liked),
        },
        "playlists": {
            "title": playlists_copy.get("title", "我的歌单"),
            "items": [playlist_summary(playlists[i]) for i in playlist_ids if i in playlists],
        },
    }


@router.get("/library/albums", response_model=AlbumListOut, summary="专辑视图（按专辑聚合曲库）")
def list_albums(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)) -> dict:
    songs = db.scalars(select(Song).order_by(Song.added_order)).all()
    grouped: dict[str, dict] = {}
    for song in songs:
        key = song.album or "未知专辑"
        bucket = grouped.setdefault(
            key,
            {
                "name": key,
                "artist": song.artist,
                "cover": song.cover,
                "song_count": 0,
                "duration": 0,
                "track_ids": [],
            },
        )
        bucket["song_count"] += 1
        bucket["duration"] += song.duration
        bucket["track_ids"].append(song.id)

    items = list(grouped.values())[:limit]
    return {"total": len(grouped), "items": items}
