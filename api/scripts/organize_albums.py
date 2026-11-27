#!/usr/bin/env python3
"""把曲库里「未知专辑」的戏腔歌曲整理成 5 张主题合集。

背景：这批 113 首 MP3 的内嵌专辑标签大多是单曲名（111 个不同值），
直接沿用会让专辑视图变成一长串只有 1 首歌的专辑，因此按曲风/主题
人工归类成合集，并写入 songs.album / songs.album_artist。

用法：
    RHYTHM_DATABASE_URL=sqlite:////path/to/rhythm.db \
        python scripts/organize_albums.py --dry-run
    RHYTHM_DATABASE_URL=sqlite:////path/to/rhythm.db \
        python scripts/organize_albums.py

幂等：重复执行只会重写同样的专辑名，不会新增歌曲或资源。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import inspect, select, text  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.models import ContentBlock, Song  # noqa: E402

ALBUM_ARTIST = "戏腔典藏"

# 顺序即专辑视图的展示顺序；(合集名, 简介, 年份, 歌曲编号)
ALBUMS: list[tuple[str, str, str, list[int]]] = [
    (
        "戏腔典藏 · 粉墨登场",
        "一台锣鼓半台戏。收录戏子行当、红妆水袖与梨园旧事，开口即是满堂彩。",
        "2026",
        [
            1, 6, 16, 17, 19, 20, 21, 22, 26, 28, 34, 41,
            42, 50, 52, 61, 65, 76, 87, 96, 99, 103, 110, 112,
        ],
    ),
    (
        "戏腔典藏 · 江湖夜雨",
        "少年提剑，快意恩仇。江湖市井、侠骨柔肠与一壶浊酒，都在这一张里。",
        "2026",
        [
            10, 12, 13, 15, 25, 32, 33, 36, 39, 43, 56, 73,
            81, 84, 86, 89, 95, 97, 105, 106,
        ],
    ),
    (
        "戏腔典藏 · 山河故梦",
        "从长安到金陵，从虞姬到木兰。唱尽史书里的名字与山川里的事。",
        "2026",
        [
            5, 37, 44, 48, 57, 58, 59, 64, 70, 71,
            79, 82, 85, 91, 93, 102, 104, 107, 108, 109,
        ],
    ),
    (
        "戏腔典藏 · 相思成笺",
        "一纸情长，半生离索。写不完的相思，唱不尽的故人与旧梦。",
        "2026",
        [
            3, 7, 8, 9, 14, 23, 29, 38, 40, 45, 46, 47, 49, 53,
            54, 62, 63, 66, 67, 69, 72, 74, 92, 94, 98, 101, 111, 113,
        ],
    ),
    (
        "戏腔典藏 · 月下清欢",
        "山水风物，闲来听雨。适合夜半一盏茶、一窗月的那一辑。",
        "2026",
        [
            2, 4, 11, 18, 24, 27, 30, 31, 35, 51, 55,
            60, 68, 75, 77, 78, 80, 83, 88, 90, 100,
        ],
    ),
]


def song_id_of(number: int) -> str:
    return f"local-xq-{number:03d}"


def ensure_album_artist_column() -> bool:
    """老库没有 album_artist 字段时补上；返回是否新建。"""
    columns = {col["name"] for col in inspect(engine).get_columns("songs")}
    if "album_artist" in columns:
        return False
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE songs ADD COLUMN album_artist VARCHAR(120) DEFAULT ''")
        )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="把戏腔曲库整理成主题合集专辑")
    parser.add_argument("--dry-run", action="store_true", help="只打印结果，不写库")
    args = parser.parse_args()

    mapping: dict[str, tuple[str, int]] = {}
    for name, _desc, _year, numbers in ALBUMS:
        for number in numbers:
            song_id = song_id_of(number)
            if song_id in mapping:
                raise SystemExit(f"歌曲编号重复：{number} 同时出现在两张专辑里")
            mapping[song_id] = (name, number)

    # ORM 一查 songs 就会带上 album_artist，列缺失时连 dry-run 都跑不起来，先补列
    if ensure_album_artist_column():
        print("[albums] 已新增 songs.album_artist 字段")

    with SessionLocal() as db:
        songs = {song.id: song for song in db.scalars(select(Song)).all()}
        missing = [sid for sid in mapping if sid not in songs]
        if missing:
            raise SystemExit(f"库里缺少这些歌曲：{', '.join(sorted(missing))}")
        uncovered = sorted(set(songs) - set(mapping))

        for song_id, (name, _number) in mapping.items():
            song = songs[song_id]
            song.album = name
            song.album_artist = ALBUM_ARTIST

        payload = {
            "artist": ALBUM_ARTIST,
            "items": [
                {"name": name, "desc": desc, "year": year, "artist": ALBUM_ARTIST}
                for name, desc, year, _numbers in ALBUMS
            ],
        }
        if not args.dry_run:
            block = db.get(ContentBlock, "albums")
            if block is None:
                db.add(ContentBlock(key="albums", payload=json.dumps(payload, ensure_ascii=False)))
            else:
                block.payload = json.dumps(payload, ensure_ascii=False)
            db.commit()

        print(f"[albums] 覆盖歌曲 {len(mapping)} / {len(songs)} 首")
        if uncovered:
            names = ", ".join(f"{songs[sid].title}({sid})" for sid in uncovered)
            print(f"[albums] 未归类：{names}")
        for name, _desc, _year, numbers in ALBUMS:
            print(f"  {name}: {len(numbers)} 首")
        if args.dry_run:
            print("[albums] dry-run，未写库")


if __name__ == "__main__":
    main()
