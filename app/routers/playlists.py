"""歌单：列表、详情、播放全部 / 随机播放。

歌单按 owner_id 隔离：只能看到自己的歌单（以及 owner_id 为空的系统歌单）。
"""

from __future__ import annotations

import random

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user, user_id_of
from ..models import Playlist, PlaylistTrack, User
from ..schemas import PlayerOut, PlaylistDetailOut, PlaylistListOut, PlayRequest
from ..services import (
    favorite_ids,
    get_user_playlist,
    player_payload,
    playlist_detail,
    playlist_summary,
    set_queue,
)

router = APIRouter(tags=["playlists"])


def _track_counts(db: Session, ids: list[str]) -> dict[str, int]:
    if not ids:
        return {}
    rows = db.execute(
        select(PlaylistTrack.playlist_id, func.count())
        .where(PlaylistTrack.playlist_id.in_(ids))
        .group_by(PlaylistTrack.playlist_id)
    ).all()
    return {playlist_id: count for playlist_id, count in rows}


@router.get("/playlists", response_model=PlaylistListOut, summary="我的歌单（可按 ids 过滤）")
def list_playlists(
    ids: str | None = Query(None, description="逗号分隔的歌单 id"),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    uid = user_id_of(user)
    stmt = select(Playlist).where(or_(Playlist.owner_id == uid, Playlist.owner_id.is_(None)))
    if ids:
        wanted = [item.strip() for item in ids.split(",") if item.strip()]
        if not wanted:
            return {"total": 0, "items": []}
        stmt = stmt.where(Playlist.id.in_(wanted))

    playlists = db.scalars(stmt.order_by(Playlist.position)).all()
    counts = _track_counts(db, [p.id for p in playlists])
    return {
        "total": len(playlists),
        "items": [playlist_summary(p, counts.get(p.id, 0)) for p in playlists],
    }


@router.get("/playlists/{playlist_id}", response_model=PlaylistDetailOut, summary="歌单详情（含曲目）")
def get_playlist_detail(
    playlist_id: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    uid = user_id_of(user)
    playlist = get_user_playlist(db, uid, playlist_id) if uid else None
    if playlist is None:
        stmt = select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id.is_(None))
        playlist = db.scalars(stmt).first()
    if playlist is None:
        from ..errors import not_found

        raise not_found(f"歌单不存在：{playlist_id}", code="playlist_not_found")
    return playlist_detail(playlist, favorite_ids(db, uid))


@router.post("/playlists/{playlist_id}/play", response_model=PlayerOut, summary="播放全部")
def play_playlist(
    playlist_id: str,
    body: PlayRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    playlist = get_user_playlist(db, user.id, playlist_id)
    track_ids = [track.song_id for track in playlist.tracks]
    if not track_ids:
        return player_payload(db, user.id)

    start = 0
    if body is not None and body.song_id:
        start = track_ids.index(body.song_id) if body.song_id in track_ids else 0
    set_queue(db, user.id, track_ids, start_index=start, autoplay=True)
    return player_payload(db, user.id)


@router.post("/playlists/{playlist_id}/shuffle", response_model=PlayerOut, summary="随机播放")
def shuffle_playlist(
    playlist_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    playlist = get_user_playlist(db, user.id, playlist_id)
    track_ids = [track.song_id for track in playlist.tracks]
    if not track_ids:
        return player_payload(db, user.id)

    random.shuffle(track_ids)
    set_queue(db, user.id, track_ids, start_index=0, autoplay=True)
    return player_payload(db, user.id)
