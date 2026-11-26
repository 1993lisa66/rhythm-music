"""离线下载，按用户隔离。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Download, Song, User
from ..schemas import DownloadCreate, DownloadListOut
from ..services import download_bytes, favorite_ids, get_song, song_out

router = APIRouter(tags=["downloads"])


def _payload(db: Session, user_id: str) -> dict:
    rows = db.execute(
        select(Download, Song)
        .join(Song, Song.id == Download.song_id)
        .where(Download.user_id == user_id)
        .order_by(Download.created_at.desc())
    ).all()
    liked = favorite_ids(db, user_id)
    items = []
    total_mb = 0.0
    for download, song in rows:
        row = song_out(song, liked)
        row["size"] = download.size
        row["downloaded_at"] = download.created_at
        items.append(row)
        total_mb += download_bytes(download.size)
    return {"total": len(items), "total_size": f"{total_mb:.1f} MB", "items": items}


@router.get("/downloads", response_model=DownloadListOut, summary="已下载列表")
def list_downloads(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return _payload(db, user.id)


@router.post("/downloads", response_model=DownloadListOut, summary="加入下载（按曲目时长估算体积）")
def add_download(
    body: DownloadCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    song = get_song(db, body.song_id)
    size = body.size or f"{max(song.duration, 1) * 0.019:.1f} MB"

    row = db.get(Download, (user.id, body.song_id))
    if row is None:
        db.add(Download(user_id=user.id, song_id=body.song_id, size=size))
    else:
        row.size = size
    db.commit()
    return _payload(db, user.id)


@router.delete("/downloads/{song_id}", response_model=DownloadListOut, summary="删除单条下载")
def remove_download(
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_song(db, song_id)
    db.execute(
        delete(Download).where(Download.user_id == user.id, Download.song_id == song_id)
    )
    db.commit()
    return _payload(db, user.id)


@router.delete("/downloads", response_model=DownloadListOut, summary="清空下载")
def clear_downloads(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    db.execute(delete(Download).where(Download.user_id == user.id))
    db.commit()
    return _payload(db, user.id)
