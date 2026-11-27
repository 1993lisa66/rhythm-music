"""歌单：列表、详情、播放全部 / 随机播放。

歌单按 owner_id 隔离：只能看到自己的歌单（以及 owner_id 为空的系统歌单）。
"""

from __future__ import annotations

import random
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user, user_id_of
from ..errors import forbidden, not_found
from ..models import Playlist, PlaylistTrack, Song, User
from ..schemas import (
    ClearOut,
    PlayerOut,
    PlaylistCreateIn,
    PlaylistDetailOut,
    PlaylistListOut,
    PlaylistTracksIn,
    PlaylistUpdateIn,
    PlayRequest,
)
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


def _editable(db: Session, user: User, playlist_id: str) -> Playlist:
    """取歌单并校验归属：系统歌单与别人的歌单都不可编辑。"""
    playlist = get_user_playlist(db, user.id, playlist_id)
    if playlist.owner_id != user.id:
        raise forbidden("只能编辑自己的歌单", code="playlist_forbidden")
    return playlist


def _sync_meta(db: Session, playlist: Playlist) -> None:
    """按曲库真实数据重算曲目数与总时长，保证列表文案与详情一致。"""
    total = db.scalar(
        select(func.coalesce(func.sum(Song.duration), 0))
        .select_from(PlaylistTrack)
        .join(Song, Song.id == PlaylistTrack.song_id)
        .where(PlaylistTrack.playlist_id == playlist.id)
    ) or 0
    count = db.scalar(
        select(func.count())
        .select_from(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist.id)
    ) or 0
    playlist.total_count = count
    minutes = max(1, round(total / 60)) if total else 0
    playlist.duration_text = f"{minutes} 分钟"


def _detail(db: Session, user: User, playlist_id: str) -> dict:
    # 会话是 expire_on_commit=False，写操作后 playlist.tracks 可能还是旧缓存，
    # 这里统一失效关系强制回库重读，保证「添加/移除后立即返回最新曲目」。
    db.expire_all()
    playlist = get_user_playlist(db, user.id, playlist_id)
    payload = playlist_detail(playlist, favorite_ids(db, user.id))
    payload["owned"] = playlist.owner_id == user.id
    return payload


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


@router.post("/playlists", response_model=PlaylistDetailOut, status_code=201, summary="创建歌单")
def create_playlist(
    body: PlaylistCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    title = body.title.strip() or "未命名歌单"
    last_position = db.scalar(
        select(func.max(Playlist.position)).where(Playlist.owner_id == user.id)
    )
    playlist = Playlist(
        id=f"pl-{uuid4().hex[:10]}",
        owner_id=user.id,
        title=title,
        badge="我的歌单",
        creator=user.name or "我",
        total_count=0,
        duration_text="0 分钟",
        desc=(body.desc or "").strip(),
        info="",
        cover="",
        tone="primary",
        position=(last_position or 0) + 1,
    )
    db.add(playlist)
    db.commit()
    return _detail(db, user, playlist.id)


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
        raise not_found(f"歌单不存在：{playlist_id}", code="playlist_not_found")
    db.expire(playlist, ["tracks"])
    payload = playlist_detail(playlist, favorite_ids(db, uid))
    payload["owned"] = bool(uid) and playlist.owner_id == uid
    return payload


@router.patch("/playlists/{playlist_id}", response_model=PlaylistDetailOut, summary="编辑歌单")
def update_playlist(
    playlist_id: str,
    body: PlaylistUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    playlist = _editable(db, user, playlist_id)
    if body.title is not None:
        title = body.title.strip()
        if title:
            playlist.title = title
    if body.desc is not None:
        playlist.desc = body.desc.strip()
    db.commit()
    return _detail(db, user, playlist_id)


@router.delete("/playlists/{playlist_id}", response_model=ClearOut, summary="删除歌单")
def delete_playlist(
    playlist_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    playlist = _editable(db, user, playlist_id)
    db.delete(playlist)
    db.commit()
    return {"cleared": True}


@router.post(
    "/playlists/{playlist_id}/tracks",
    response_model=PlaylistDetailOut,
    summary="向歌单添加歌曲（自动跳过重复与不存在的曲目）",
)
def add_playlist_tracks(
    playlist_id: str,
    body: PlaylistTracksIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    playlist = _editable(db, user, playlist_id)
    wanted = [song_id for song_id in dict.fromkeys(body.song_ids) if song_id]
    if not wanted:
        return _detail(db, user, playlist_id)

    valid = set(db.scalars(select(Song.id).where(Song.id.in_(wanted))).all())
    existing = {track.song_id for track in playlist.tracks}
    position = max((track.position for track in playlist.tracks), default=-1) + 1

    added = 0
    for song_id in wanted:
        if song_id in existing or song_id not in valid:
            continue
        db.add(PlaylistTrack(playlist_id=playlist.id, song_id=song_id, position=position))
        position += 1
        existing.add(song_id)
        added += 1

    if added:
        db.flush()
        _sync_meta(db, playlist)
        db.commit()
        # 让关系缓存失效，下面的 _detail 才能读到刚加入的曲目
        db.expire(playlist, ["tracks"])
    return _detail(db, user, playlist_id)


@router.delete(
    "/playlists/{playlist_id}/tracks/{song_id}",
    response_model=PlaylistDetailOut,
    summary="从歌单移除歌曲",
)
def remove_playlist_track(
    playlist_id: str,
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    playlist = _editable(db, user, playlist_id)
    track = next((item for item in playlist.tracks if item.song_id == song_id), None)
    if track is None:
        raise not_found("歌单里没有这首歌", code="track_not_found")
    db.delete(track)
    db.flush()
    _sync_meta(db, playlist)
    db.commit()
    db.expire(playlist, ["tracks"])
    return _detail(db, user, playlist_id)


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
