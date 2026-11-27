"""聚合页：发现首页、音乐库（含专辑视图）。歌单取自当前用户自己的克隆。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..deps import get_optional_user, user_id_of
from ..models import Playlist, Song, User
from ..schemas import (
    AlbumDetailOut,
    AlbumListOut,
    ArtistDetailOut,
    DiscoverOut,
    LibraryOut,
)
from ..services import favorite_ids, get_content, playlist_summary, recent_groups, song_out

router = APIRouter(tags=["browse"])

DISCOVER_RECENT_LIMIT = 10


def _songs_by_ids(db: Session, ids: list[str], liked: set[str]) -> list[dict]:
    if not ids:
        return []
    found = {song.id: song for song in db.scalars(select(Song).where(Song.id.in_(ids))).all()}
    return [song_out(found[i], liked) for i in ids if i in found]


def _owned_playlists(db: Session, user_id: str | None) -> list[Playlist]:
    if not user_id:
        return []
    return list(
        db.scalars(
            select(Playlist)
            .where(Playlist.owner_id == user_id)
            .order_by(Playlist.position)
        ).all()
    )


@router.get("/discover", response_model=DiscoverOut, summary="发现首页聚合")
def get_discover(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    content = get_content(db, "discover")
    liked = favorite_ids(db, user_id_of(user))

    featured_copy = content.get("featured", {})
    owned = _owned_playlists(db, user_id_of(user))
    featured_playlist = None
    if owned:
        template_id = featured_copy.get("playlistId")
        match = next((p for p in owned if p.id.endswith(f"-{template_id}")), None)
        featured_playlist = playlist_summary(match or owned[0])

    recent_copy = content.get("recent", {})
    moods_copy = content.get("moods", {})

    # 问候语按时段固定，名字换成当前用户（未登录时保留文案原样）
    greeting = content.get("greeting", "")
    if user is not None and greeting:
        greeting = f"{greeting.split('，')[0]}，{user.name}"

    # 发现页的「最近播放」取当前用户自己的播放记录；匿名时才回落到文案里的示例曲目
    if user is not None:
        flat = [item for group in recent_groups(db, user.id, per_group=6) for item in group["items"]]
        recent_items = flat[:DISCOVER_RECENT_LIMIT]
    else:
        recent_items = _songs_by_ids(db, content.get("recent", {}).get("songIds", []), liked)

    return {
        "greeting": greeting,
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
            "items": recent_items,
        },
    }


@router.get("/library", response_model=LibraryOut, summary="音乐库聚合")
def get_library(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    content = get_content(db, "library")
    liked = favorite_ids(db, user_id_of(user))

    recent_copy = content.get("recent", {})
    playlists_copy = content.get("playlists", {})
    wanted = playlists_copy.get("ids", [])
    owned = _owned_playlists(db, user_id_of(user))
    # 先按文案里的顺序排（private / commute 等），其余歌单全部追加，避免列表被截断
    picked: list[Playlist] = []
    for template_id in wanted:
        match = next((p for p in owned if p.id.endswith(f"-{template_id}")), None)
        if match is not None and match not in picked:
            picked.append(match)
    for playlist in owned:
        if playlist not in picked:
            picked.append(playlist)

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
            "items": [playlist_summary(p) for p in picked],
        },
    }


UNKNOWN_ALBUM = "未知专辑"


def _album_copy(db: Session) -> dict[str, dict]:
    """专辑文案（简介 / 年份 / 展示顺序），由 organize_albums.py 写入 content_blocks。"""
    block = get_content(db, "albums")
    return {item.get("name", ""): item for item in block.get("items", [])}


def _albums(db: Session) -> list[dict]:
    """按歌曲 album 分组，顺序优先跟随文案，其余按曲目数倒序。"""
    copy = _album_copy(db)
    songs = db.scalars(select(Song).order_by(Song.added_order)).all()
    grouped: dict[str, dict] = {}
    for song in songs:
        key = song.album or UNKNOWN_ALBUM
        bucket = grouped.get(key)
        if bucket is None:
            bucket = grouped[key] = {
                "name": key,
                "artist": song.album_artist or song.artist,
                "cover": config.asset_url(song.cover),
                "song_count": 0,
                "duration": 0,
                "track_ids": [],
                "desc": copy.get(key, {}).get("desc", ""),
                "year": copy.get(key, {}).get("year", ""),
            }
        bucket["song_count"] += 1
        bucket["duration"] += song.duration
        bucket["track_ids"].append(song.id)

    order = list(copy.keys())
    return sorted(
        grouped.values(),
        key=lambda a: (
            order.index(a["name"]) if a["name"] in order else len(order),
            -a["song_count"],
        ),
    )


@router.get("/library/albums", response_model=AlbumListOut, summary="专辑视图（按专辑聚合曲库）")
def list_albums(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)) -> dict:
    items = _albums(db)
    return {"total": len(items), "items": items[:limit]}


@router.get(
    "/library/albums/{name}",
    response_model=AlbumDetailOut,
    summary="专辑详情（含曲目）",
)
def get_album(
    name: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    album = next((item for item in _albums(db) if item["name"] == name), None)
    if album is None:
        raise HTTPException(status_code=404, detail="专辑不存在")
    liked = favorite_ids(db, user_id_of(user))
    found = {
        song.id: song
        for song in db.scalars(select(Song).where(Song.id.in_(album["track_ids"]))).all()
    }
    tracks = []
    for index, song_id in enumerate(album["track_ids"]):
        song = found.get(song_id)
        if song is None:
            continue
        row = song_out(song, liked)
        row["index"] = index
        tracks.append(row)
    album["tracks"] = tracks
    return album


@router.get(
    "/artists/{name}",
    response_model=ArtistDetailOut,
    summary="歌手详情（该歌手的全部曲目）",
)
def get_artist(
    name: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    songs = db.scalars(
        select(Song).where(Song.artist == name).order_by(Song.added_order)
    ).all()
    # 「戏腔典藏」这类是合集名（album_artist），不挂在单曲艺人上：artist 查不到时按合集兜底
    if not songs:
        songs = db.scalars(
            select(Song).where(Song.album_artist == name).order_by(Song.added_order)
        ).all()
    if not songs:
        raise HTTPException(status_code=404, detail="歌手不存在")
    liked = favorite_ids(db, user_id_of(user))
    total = sum(song.duration for song in songs)
    minutes, seconds = divmod(total, 60)
    duration_text = (
        f"{minutes // 60} 小时 {minutes % 60} 分钟" if minutes >= 60 else f"{minutes} 分钟"
    )
    return {
        "name": name,
        "cover": config.asset_url(songs[0].cover),
        "song_count": len(songs),
        "album_count": len({song.album for song in songs if song.album}),
        "duration": total,
        "duration_text": duration_text,
        "tracks": [
            {**song_out(song, liked), "index": index}
            for index, song in enumerate(songs)
        ],
    }
