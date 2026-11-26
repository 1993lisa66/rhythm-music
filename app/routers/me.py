"""我的：资料卡、统计、菜单入口、设置。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ProfileOut, SettingsOut, SettingsPatch
from ..services import computed_stats, get_content, settings_payload, update_settings

router = APIRouter(tags=["me"])

# 菜单项 → 前端路由，避免把路由写死在数据里
MENU_ROUTES = {
    "我的收藏": "/playlist/private",
    "最近播放": "/recent",
    "离线下载": "/downloads",
    "我的歌单": "/mylists",
}

# 菜单项 → 真实数量字段（value 文案沿用设计稿，count 给真实值）
MENU_COUNTS = {
    "我的收藏": "favorites",
    "最近播放": "today_plays",
    "离线下载": "downloads",
    "我的歌单": "playlists",
}


@router.get("/me/profile", response_model=ProfileOut, summary="我的页资料 / 统计 / 菜单")
def get_profile(db: Session = Depends(get_db)) -> dict:
    content = get_content(db, "profile")
    computed = computed_stats(db)

    menu_copy = content.get("menu", {})
    items = []
    for item in menu_copy.get("items", []):
        name = item.get("name", "")
        items.append(
            {
                "icon": item.get("icon", ""),
                "name": name,
                "value": item.get("value", ""),
                "route": MENU_ROUTES.get(name, "/library"),
                "count": computed.get(MENU_COUNTS.get(name, "songs")) or 0,
            }
        )

    return {
        "title": content.get("title", "我的"),
        "user": content.get(
            "user",
            {"name": "阿韵", "id": "ID: 8823 6102", "member": "音乐会员", "avatar": ""},
        ),
        "stats": content.get("stats", []),
        "menu": {"title": menu_copy.get("title", "我的音乐"), "items": items},
        "computed": computed,
    }


@router.get("/me/settings", response_model=SettingsOut, summary="播放设置")
def get_settings(db: Session = Depends(get_db)) -> dict:
    return settings_payload(db)


@router.patch("/me/settings", response_model=SettingsOut, summary="修改设置（字段可选）")
def patch_settings(body: SettingsPatch, db: Session = Depends(get_db)) -> dict:
    patch = body.model_dump(exclude_none=True)
    if not patch:
        return settings_payload(db)
    return update_settings(db, **patch)
