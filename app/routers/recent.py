"""最近播放：按 今天 / 昨天 / 更早 分组，按用户隔离。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import PlayEvent, User
from ..schemas import ClearOut, RecentOut, RecordOut
from ..services import get_content, recent_groups, record_play

router = APIRouter(tags=["recent"])


@router.get("/recent", response_model=RecentOut, summary="最近播放（分组，同曲只保留最近一次）")
def get_recent(
    per_group: int = Query(20, ge=1, le=100, description="每组最多返回多少条"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    content = get_content(db, "recent")
    groups = recent_groups(db, user.id, per_group=per_group)
    return {
        "title": content.get("title", "最近播放"),
        "total": sum(group["count"] for group in groups),
        "groups": groups,
    }


@router.post("/recent/{song_id}", response_model=RecordOut, summary="记录一次播放")
def record(
    song_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    played_at = record_play(db, user.id, song_id)
    return {"recorded": True, "song_id": song_id, "played_at": played_at}


@router.delete("/recent", response_model=ClearOut, summary="清空最近播放")
def clear_recent(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    db.execute(delete(PlayEvent).where(PlayEvent.user_id == user.id))
    db.commit()
    return {"cleared": True}
