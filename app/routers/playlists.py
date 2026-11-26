"""歌单：列表、详情、播放全部 / 随机播放。"""

from __future__ import annotations

import random

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Playlist, PlaylistTrack
from ..schemas import PlayerOut, PlaylistDetailOut, PlaylistListOut, PlayRequest
from ..services import (
    favorite_ids,
    get_playlist,
    player_payload,
    playlist_detail,
    playlist_summary,
    set_queue,
)

router = APIRouter(tags=["playlists"])


def _track_counts(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(PlaylistTrack.playlist_id, func.count()).group_by(PlaylistTrack.playlist_id)
    ).all()
    return {playlist_id: count for playlist_id, count in rows}


@router.get("/playlists", response_model=PlaylistListOut, summary="歌单列表（可按 ids 过滤）")
def list_playlists(
    ids: str | None = Query(None, description="逗号分隔，如 private,commute"),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Playlist).order_by(Playlist.position)
    if ids:
        wanted = [item.strip() for item in ids.split(",") if item.strip()]
        if not wanted:
            return {"total": 0, "items": []}
        stmt = select(Playlist).where(Playlist.id.in_(wanted)).order_by(Playlist.position)

    playlists = db.scalars(stmt).all()
    counts = _track_counts(db)
    return {
        "total": len(playlists),
        "items": [playlist_summary(p, counts.get(p.id, 0)) for p in playlists],
    }


@router.get("/playlists/{playlist_id}", response_model=PlaylistDetailOut, summary="歌单详情（含曲目）")
def get_playlist_detail(playlist_id: str, db: Session = Depends(get_db)) -> dict:
    return playlist_detail(get_playlist(db, playlist_id), favorite_ids(db))


@router.post("/playlists/{playlist_id}/play", response_model=PlayerOut, summary="播放全部")
def play_playlist(
    playlist_id: str,
    body: PlayRequest | None = None,
    db: Session = Depends(get_db),
) -> dict:
    playlist = get_playlist(db, playlist_id)
    track_ids = [track.song_id for track in playlist.tracks]
    if not track_ids:
        return player_payload(db)

    start = 0
    if body is not None and body.song_id:
        start = track_ids.index(body.song_id) if body.song_id in track_ids else 0
    set_queue(db, track_ids, start_index=start, autoplay=True)
    return player_payload(db)


@router.post("/playlists/{playlist_id}/shuffle", response_model=PlayerOut, summary="随机播放")
def shuffle_playlist(playlist_id: str, db: Session = Depends(get_db)) -> dict:
    playlist = get_playlist(db, playlist_id)
    track_ids = [track.song_id for track in playlist.tracks]
    if not track_ids:
        return player_payload(db)

    random.shuffle(track_ids)
    set_queue(db, track_ids, start_index=0, autoplay=True)
    return player_payload(db)
