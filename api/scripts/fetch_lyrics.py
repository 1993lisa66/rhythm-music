#!/usr/bin/env python3
"""批量在线查找歌词。

按歌名 / 歌手 / 时长向 LRCLIB 精确匹配，命中才写入 lyric_lines；未收录的保持空，
不生成任何猜测歌词。结束后把全部歌词回写 data/seed/lyrics.json，保证重建库后不丢。

用法：
    python scripts/fetch_lyrics.py                 # 查全部歌曲
    python scripts/fetch_lyrics.py --prefix s      # 只查 s 开头的歌曲
    python scripts/fetch_lyrics.py --workers 3     # 并发数
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import delete, select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.lyrics_source import fetch_lyrics  # noqa: E402
from app.models import LyricLine, Song  # noqa: E402


def lookup(song: Song) -> tuple[str, list[dict], str]:
    try:
        lines = fetch_lyrics(song.title, song.artist, song.duration)
        return song.id, lines, ""
    except Exception as error:  # 单首失败不影响整批
        return song.id, [], f"{type(error).__name__}: {error}"


def dump_seed(db) -> int:
    payload: dict[str, dict] = {}
    rows = db.scalars(select(LyricLine).order_by(LyricLine.song_id, LyricLine.position)).all()
    for row in rows:
        payload.setdefault(row.song_id, {"lines": []})["lines"].append(
            {"t": row.t, "text": row.text}
        )
    path = BASE_DIR / "data" / "seed" / "lyrics.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="批量在线查找歌词（LRCLIB）")
    parser.add_argument("--prefix", default="", help="只处理指定前缀的歌曲 id")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.2, help="每完成一次查询后的间隔秒数")
    args = parser.parse_args()

    with SessionLocal() as db:
        stmt = select(Song)
        if args.prefix:
            stmt = stmt.where(Song.id.like(f"{args.prefix}%"))
        songs = db.scalars(stmt).all()
        already = set(db.scalars(select(LyricLine.song_id).distinct()).all())
    songs = [song for song in songs if song.id not in already]
    titles = {song.id: song.title for song in songs}
    print(f"待查 {len(songs)} 首（已有歌词 {len(already)} 首）", flush=True)

    found: list[tuple[str, list[dict]]] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(lookup, song): song for song in songs}
        for index, future in enumerate(as_completed(futures), 1):
            song_id, lines, error = future.result()
            if lines:
                found.append((song_id, lines))
            elif error:
                errors.append(f"{titles.get(song_id, song_id)}: {error}")
            if index % 50 == 0:
                print(f"已查 {index}/{len(songs)}，命中 {len(found)}", flush=True)
            time.sleep(args.delay)

    with SessionLocal() as db:
        for song_id, lines in found:
            db.execute(delete(LyricLine).where(LyricLine.song_id == song_id))
            db.add_all(
                [
                    LyricLine(song_id=song_id, position=i, t=item["t"], text=item["text"])
                    for i, item in enumerate(lines)
                ]
            )
        db.commit()
        total = dump_seed(db)

    print(f"\n完成：命中 {len(found)} 首，失败 {len(errors)} 次，歌词总行数 {total}")
    if errors:
        print("失败示例：", errors[:5])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
