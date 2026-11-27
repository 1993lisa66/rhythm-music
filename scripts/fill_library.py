#!/usr/bin/env python3
"""给已导入的曲库补齐封面、歌单与发现页文案。

做三件事：
1. 从 MP3 内嵌 APIC 提取封面，上传 OSS covers/<song_id>.jpg，写入 songs.cover；
2. 为现有用户创建戏腔歌单（含今日推荐 featured 歌单）并填充曲目；
3. 把 content_blocks 里失效的旧歌单 / 歌曲 ID 换成现有曲库，补齐播放队列与最近播放。

用法：
    RHYTHM_DATABASE_URL=sqlite:////path/to/rhythm.db \
        python scripts/fill_library.py --source "/path/to/music" --dry-run
    RHYTHM_DATABASE_URL=sqlite:////path/to/rhythm.db \
        python scripts/fill_library.py --source "/path/to/music"

注意：只更新空封面，不覆盖已有封面；歌单按固定 ID 幂等创建/补齐。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import config  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    ContentBlock,
    PlayEvent,
    PlayerState,
    Playlist,
    PlaylistTrack,
    QueueItem,
    Song,
    User,
)
from upload_assets import remote_size, upload  # noqa: E402

# 今日推荐的歌单必须叫 xiqu-best，与 discover 文案的 featured.playlistId 对应
PLAYLISTS = [
    {
        "id": "xiqu-best",
        "title": "戏腔精选 · 一曲咿呀唱尽戏子悲与泪",
        "badge": "私藏合辑",
        "featured_badge": "编辑精选",
        "desc": "一曲咿呀，唱尽戏子悲欢与浮生帘梦。",
        "info": "戏腔精选 · 113 首",
        "tone": "sunset",
        "pick": lambda rows: rows[:12],
    },
    {
        "id": "xiqu-classic",
        "title": "经典戏腔 · 百听不厌",
        "badge": "场景歌单",
        "featured_badge": None,
        "desc": "从《牵丝戏》到《典狱司》，每段唱腔都是一段故事。",
        "info": "经典唱段 · 常听常新",
        "tone": "warm",
        "pick": lambda rows: rows[12:32],
    },
    {
        "id": "xiqu-duet",
        "title": "对唱戏腔 · 男女和声",
        "badge": "场景歌单",
        "featured_badge": None,
        "desc": "一唱一和，戏台上的相逢。",
        "info": "男女对唱 · 婉转相和",
        "tone": "sage",
        "pick": lambda rows: rows[32:48],
    },
    {
        "id": "xiqu-night",
        "title": "夜听戏腔 · 婉转萦绕",
        "badge": "心情歌单",
        "featured_badge": None,
        "desc": "夜深时听一曲，浓韵萦绕，久久不散。",
        "info": "夜深人静 · 慢慢听",
        "tone": "plum",
        "pick": lambda rows: rows[48:64],
    },
]

MOODS = [
    {"name": "戏腔", "tone": "sage", "genre": "戏腔"},
    {"name": "古风", "tone": "honey", "genre": "戏腔"},
    {"name": "唱段", "tone": "plum", "genre": "戏腔"},
]


def local_audio(source: Path, song_id: str) -> Path | None:
    """按 song_id 尾号匹配本地「编号.歌名 - 歌手.mp3」。"""
    match = re.search(r"(\d+)$", song_id)
    if not match:
        return None
    number = int(match.group(1))
    for path in source.glob("*.mp3"):
        head = path.stem.split(".", 1)[0]
        if head.isdigit() and int(head) == number:
            return path
    return None


def embedded_cover(path: Path) -> tuple[bytes, str] | None:
    try:
        from mutagen.mp3 import MP3

        audio = MP3(path)
        for key, frame in (audio.tags or {}).items():
            if key.startswith("APIC") and frame.data:
                mime = frame.mime or "image/jpeg"
                ext = "png" if "png" in mime else "jpg"
                return frame.data, ext
    except Exception:
        return None
    return None


def fill_covers(db: Session, source: Path, dry_run: bool) -> int:
    songs = db.scalars(select(Song).where(Song.cover == "")).all()
    print(f"待补封面 {len(songs)} 首", flush=True)
    filled = 0
    for song in songs:
        path = local_audio(source, song.id)
        if path is None:
            print(f"  未找到音频：{song.id}", flush=True)
            continue
        result = embedded_cover(path)
        if result is None:
            print(f"  无内嵌封面：{song.id}", flush=True)
            continue
        data, ext = result
        key = f"covers/{song.id}.{ext}"
        if not dry_run:
            if remote_size(key) != len(data):
                upload(key, data, "image/png" if ext == "png" else "image/jpeg")
            song.cover = f"/{key}"
            db.flush()
        filled += 1
    if not dry_run:
        db.commit()
    return filled


def fill_playlists(db: Session, dry_run: bool) -> int:
    songs = db.scalars(select(Song).order_by(Song.added_order)).all()
    users = db.scalars(select(User)).all()
    if not songs:
        print("曲库为空，跳过歌单")
        return 0
    covers = {song.id: song.cover for song in songs}
    counts = 0
    for user in users:
        for order, item in enumerate(PLAYLISTS):
            playlist_id = f"{user.id}-{item['id']}"
            playlist = db.get(Playlist, playlist_id)
            picked = item["pick"](songs)
            if not picked:
                continue
            if dry_run:
                counts += len(picked)
                continue
            if playlist is None:
                playlist = Playlist(
                    id=playlist_id,
                    owner_id=user.id,
                    title=item["title"],
                    badge=item["badge"],
                    featured_badge=item["featured_badge"],
                    creator=user.name,
                    total_count=len(picked),
                    duration_text=f"{sum(s.duration for s in picked) / 3600:.1f} 小时",
                    desc=item["desc"],
                    info=item["info"],
                    cover=covers.get(picked[0].id, ""),
                    tone=item["tone"],
                    position=order,
                )
                db.add(playlist)
                db.flush()
            else:
                # 已存在的歌单同步最新元信息（修正旧的时长/封面）
                playlist.total_count = len(picked)
                playlist.duration_text = f"{sum(s.duration for s in picked) / 3600:.1f} 小时"
                playlist.cover = covers.get(picked[0].id, "")
                playlist.info = item["info"]
            existing = set(
                db.scalars(
                    select(PlaylistTrack.position).where(PlaylistTrack.playlist_id == playlist_id)
                ).all()
            )
            for pos, song in enumerate(picked):
                if pos in existing:
                    continue
                db.add(
                    PlaylistTrack(
                        playlist_id=playlist_id,
                        song_id=song.id,
                        position=pos,
                    )
                )
                counts += 1
    if not dry_run:
        db.commit()
    return counts


def update_blocks(db: Session, songs: list[Song], dry_run: bool) -> None:
    ids = [song.id for song in songs]
    by_id = {song.id: song for song in songs}
    if not ids:
        return

    blocks = {block.key: block for block in db.scalars(select(ContentBlock)).all()}
    discover = json.loads(blocks["discover"].payload) if "discover" in blocks else {}
    discover.setdefault("featured", {})["playlistId"] = "xiqu-best"
    discover["moods"] = {"title": "随心听", "items": MOODS}
    discover.setdefault("recent", {})["songIds"] = ids[:10]

    library = json.loads(blocks["library"].payload) if "library" in blocks else {}
    library.setdefault("recent", {})["songIds"] = ids

    search = json.loads(blocks["search"].payload) if "search" in blocks else {}
    search.setdefault("hot", {})["items"] = [
        {"text": "戏腔", "tone": "primary"},
        {"text": "古风", "tone": "sage"},
        {"text": "对唱", "tone": "honey"},
        {"text": "戏腔版", "tone": "plum"},
    ]
    # 搜索页两行布局：大卡行、小卡行各 2 张（390px 设备减 48px 内边距 = 342px，
    # 两张 152px 卡 + 14px 间距 = 318px 刚好放下）；多放一张会溢出外壳。
    search.setdefault("recommend", {})["items"] = [
        {
            "id": song.id,
            "title": song.title,
            "sub": f"{song.artist} · 戏腔",
            "cover": song.cover,
            "size": "lg" if index < 2 else "sm",
        }
        for index, song in enumerate(songs[:4])
    ]

    profile = json.loads(blocks["profile"].payload) if "profile" in blocks else {}
    for stat in profile.get("stats", []):
        if stat.get("label") == "首歌":
            stat["value"] = str(len(ids))

    for key, payload in (
        ("discover", discover),
        ("library", library),
        ("search", search),
        ("profile", profile),
    ):
        block = blocks.get(key)
        if block is None:
            block = ContentBlock(key=key, payload="{}")
            db.add(block)
        if not dry_run:
            block.payload = json.dumps(payload, ensure_ascii=False)


def fill_user_state(db: Session, songs: list[Song], dry_run: bool) -> None:
    ids = [song.id for song in songs]
    if not ids:
        return
    for user in db.scalars(select(User)).all():
        if not db.scalar(select(func.count()).select_from(QueueItem).where(QueueItem.user_id == user.id)):
            if not dry_run:
                for pos, song_id in enumerate(ids[:12]):
                    db.add(QueueItem(user_id=user.id, position=pos, song_id=song_id))
        played = set(
            db.scalars(select(PlayEvent.song_id).where(PlayEvent.user_id == user.id)).all()
        )
        if not dry_run:
            base = datetime.now().replace(microsecond=0)
            # 补足到 10 首，保留用户已有的真实播放记录
            for index, song_id in enumerate(ids[:10]):
                if song_id in played:
                    continue
                db.add(
                    PlayEvent(
                        user_id=user.id,
                        song_id=song_id,
                        played_at=base - timedelta(minutes=17 + index * 23),
                    )
                )
        state = db.get(PlayerState, user.id)
        if state is not None and not dry_run:
            state.index = 0
            state.position = 0
    if not dry_run:
        db.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="补齐曲库封面、歌单与发现页文案")
    parser.add_argument("--source", required=True, help="原始歌曲目录（读取内嵌封面）")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不上传、不写库")
    args = parser.parse_args()

    source = Path(args.source).expanduser()
    if not source.is_dir():
        raise SystemExit(f"目录不存在：{source}")

    with SessionLocal() as db:
        songs = db.scalars(select(Song).order_by(Song.added_order)).all()
        print(f"曲库 {len(songs)} 首，数据库 {config.DATABASE_URL}", flush=True)
        covers = fill_covers(db, source, args.dry_run)
        tracks = fill_playlists(db, args.dry_run)
        db.flush()
        # 重新取一次，带上刚写入的 cover
        songs = db.scalars(select(Song).order_by(Song.added_order)).all()
        update_blocks(db, songs, args.dry_run)
        fill_user_state(db, songs, args.dry_run)

    print(f"完成：补封面 {covers} 张，歌单曲目 {tracks} 条，文案块已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
