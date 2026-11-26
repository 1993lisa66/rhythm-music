"""我的：资料卡、统计、菜单入口、设置。全部按当前用户计算。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Playlist, User
from ..schemas import PlaylistListOut, ProfileOut, SettingsOut, SettingsPatch
from ..services import computed_stats, get_content, settings_payload, update_settings
from .auth import user_out

router = APIRouter(tags=["me"])

# 菜单项 → 前端路由（收藏 / 最近播放 / 歌单都是独立页面）
MENU_ROUTES = {
    "我的收藏": "/favorites",
    "最近播放": "/recent",
    "我的歌单": "/mylists",
}

# 菜单项 → 真实数量字段
MENU_COUNTS = {
    "我的收藏": "favorites",
    "最近播放": "today_plays",
    "我的歌单": "playlists",
}

MENU_VALUES = {
    "我的收藏": lambda n: f"{n} 首",
    "最近播放": lambda n: f"今天 {n} 首",
    "我的歌单": lambda n: f"{n} 个",
}

STAT_LABELS = [
    ("favorites", "收藏"),
    ("playlists", "歌单"),
    ("following", "关注"),
    ("songs", "首歌"),
]


def _owned_playlist_ids(db: Session, user_id: str) -> set[str]:
    return set(
        db.scalars(select(Playlist.id).where(Playlist.owner_id == user_id)).all()
    )


@router.get("/me/profile", response_model=ProfileOut, summary="我的页资料 / 统计 / 菜单")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    content = get_content(db, "profile")
    computed = computed_stats(db, user.id)
    menu_copy = content.get("menu", {})

    items = []
    for item in menu_copy.get("items", []):
        name = item.get("name", "")
        # 只渲染代码里有对应页面的菜单项：历史文案里已下线的入口（如离线下载）不再透出
        if name not in MENU_ROUTES:
            continue
        key = MENU_COUNTS.get(name, "songs")
        count = computed.get(key) or 0
        items.append(
            {
                "icon": item.get("icon", ""),
                "name": name,
                "value": MENU_VALUES.get(name, lambda n: f"{n} 首")(count),
                "route": MENU_ROUTES.get(name, "/library"),
                "count": count,
            }
        )

    stats = [
        {"value": str(computed.get(key) or 0), "label": label}
        for key, label in STAT_LABELS
    ]

    return {
        "title": content.get("title", "我的"),
        "user": user_out(user),
        "stats": stats,
        "menu": {"title": menu_copy.get("title", "我的音乐"), "items": items},
        "computed": computed,
    }


@router.get("/me/playlists", response_model=PlaylistListOut, summary="我的歌单（按创建顺序）")
def my_playlists(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    from ..services import playlist_summary

    rows = db.scalars(
        select(Playlist).where(Playlist.owner_id == user.id).order_by(Playlist.position)
    ).all()
    return {"total": len(rows), "items": [playlist_summary(p) for p in rows]}


@router.get("/me/settings", response_model=SettingsOut, summary="播放设置")
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return settings_payload(db, user.id)


@router.patch("/me/settings", response_model=SettingsOut, summary="修改设置（字段可选）")
def patch_settings(
    body: SettingsPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    patch = body.model_dump(exclude_none=True)
    if not patch:
        return settings_payload(db, user.id)
    return update_settings(db, user.id, **patch)
