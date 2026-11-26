"""收藏（我的收藏 / 播放页心形），按用户隔离。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Favorite, Song, User
from ..schemas import FavoriteListOut, FavoriteStateOut
from ..services import favorite_ids, get_song, song_out

router = APIRouter(tags=["favorites"])


def _total(db: Session, user_id: str) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
        )
        or 0
    )


@router.get("/favorites", response_model=FavoriteListOut, summary="收藏列表")
def list_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = (
        db.execute(
            select(Song)
            .join(Favorite, Favorite.song_id == Song.id)
            .where(Favorite.user_id == user.id)
            .order_by(Favorite.created_at.desc())
        )
        .scalars()
        .all()
    )
    liked = favorite_ids(db, user.id)
    return {"total": len(rows), "items": [song_out(song, liked) for song in rows]}


@router.put("/favorites/{song_id}", response_model=FavoriteStateOut, summary="加入收藏（幂等）")
def add_favorite(
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_song(db, song_id)
    if db.get(Favorite, (user.id, song_id)) is None:
        db.add(Favorite(user_id=user.id, song_id=song_id))
        db.commit()
    return {"song_id": song_id, "liked": True, "total": _total(db, user.id)}


@router.delete("/favorites/{song_id}", response_model=FavoriteStateOut, summary="取消收藏")
def remove_favorite(
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_song(db, song_id)
    db.execute(
        delete(Favorite).where(Favorite.user_id == user.id, Favorite.song_id == song_id)
    )
    db.commit()
    return {"song_id": song_id, "liked": False, "total": _total(db, user.id)}


@router.post("/favorites/{song_id}/toggle", response_model=FavoriteStateOut, summary="收藏取反")
def toggle_favorite(
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_song(db, song_id)
    row = db.get(Favorite, (user.id, song_id))
    if row is None:
        db.add(Favorite(user_id=user.id, song_id=song_id))
        liked = True
    else:
        db.delete(row)
        liked = False
    db.commit()
    return {"song_id": song_id, "liked": liked, "total": _total(db, user.id)}


@router.get("/favorites/{song_id}", response_model=FavoriteStateOut, summary="单曲收藏状态")
def favorite_state(
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    get_song(db, song_id)
    liked = db.get(Favorite, (user.id, song_id)) is not None
    return {"song_id": song_id, "liked": liked, "total": _total(db, user.id)}
