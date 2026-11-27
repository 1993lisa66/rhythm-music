#!/usr/bin/env python3
"""导入「编号.歌名 - 歌手.mp3」目录到 OSS 和数据库，同时导入同名 .lrc 歌词。

用法：
    RHYTHM_DATABASE_URL=sqlite:////path/to/rhythm.db \
        python scripts/import_folder.py --source "/path/to/music" --dry-run
    RHYTHM_DATABASE_URL=sqlite:////path/to/rhythm.db \
        python scripts/import_folder.py --source "/path/to/music"

约定：
- 文件名形如「12.歌名 - 歌手.mp3」，编号用于生成稳定 song_id（local-xq-012）。
- 歌词文件与音频同名同目录、后缀 .lrc，按 GB18030/UTF-8 解码；时间戳转成秒写 lyric_lines。
- 音频对象键为 audio/<song_id>.mp3；远端已有同大小对象时直接复用不重传。
- 不写 data/seed/*.json，不动歌单，只新增 songs 与 lyric_lines。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from sqlalchemy import func, select  # noqa: E402

from app import config  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import LyricLine, Song  # noqa: E402
from upload_assets import CONTENT_TYPES, remote_size, upload  # noqa: E402

AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
NAME_RE = re.compile(r"^\s*(\d+)\s*[.．、]\s*(.+)$")
TIME_RE = re.compile(r"\[(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?\]")


def parse_name(path: Path) -> tuple[str, str, str]:
    """返回 (编号字符串, 歌名, 歌手)。"""
    stem = path.stem
    match = NAME_RE.match(stem)
    number = match.group(1) if match else ""
    rest = match.group(2) if match else stem
    if " - " in rest:
        title, artist = (part.strip() for part in rest.rsplit(" - ", 1))
    else:
        title, artist = rest.strip(), ""
    return number, title, artist


def base_song_id(path: Path, number: str) -> str:
    """按编号生成稳定 ID；同一文件重跑时 ID 不变，便于幂等跳过。"""
    return (
        f"local-xq-{int(number):03d}"
        if number.isdigit()
        else "local-" + hashlib.md5(path.stem.encode("utf-8")).hexdigest()[:10]
    )


def make_song_id(base: str, used: set[str]) -> str:
    candidate, index = base, 2
    while candidate in used:
        candidate, index = f"{base}-{index}", index + 1
    used.add(candidate)
    return candidate


def read_lrc(path: Path) -> list[tuple[int, str]]:
    """解析 LRC 为 (秒, 文本)；兼容 GBK/GB18030 与 UTF-8。"""
    raw = path.read_bytes()
    text = ""
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")

    lines: list[tuple[int, str]] = []
    for row in text.splitlines():
        stamps = TIME_RE.findall(row)
        if not stamps:
            continue
        label = TIME_RE.sub("", row).strip()
        if not label:
            continue
        for minute, second, fraction in stamps:
            seconds = int(minute) * 60 + int(second)
            if fraction:
                seconds += float(f"0.{fraction}")
            lines.append((int(round(seconds)), label))
    lines.sort(key=lambda item: item[0])
    return lines


def duration_of(path: Path) -> int:
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path)
        return int(getattr(audio.info, "length", 0) or 0) if audio else 0
    except Exception:
        return 0


def collect(source: Path, limit: int | None) -> list[Path]:
    if source.is_file():
        files = [source]
    elif source.is_dir():
        files = [p for p in source.iterdir() if p.is_file() and not p.name.startswith("._")]
    else:
        raise SystemExit(f"目录不存在：{source}")
    files = [p for p in files if p.suffix.lower() in AUDIO_SUFFIXES]

    def sort_key(path: Path):
        number, _, _ = parse_name(path)
        return (0, int(number), path.name) if number.isdigit() else (1, 0, path.name)

    files.sort(key=sort_key)
    return files[:limit] if limit else files


def upload_one(path: Path, key: str) -> str:
    data = path.read_bytes()
    if remote_size(key) == len(data):
        return "复用"
    upload(key, data, CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"))
    return "上传"


def main() -> int:
    parser = argparse.ArgumentParser(description="批量导入本地歌曲与 LRC 歌词")
    parser.add_argument("--source", required=True, help="音频目录或单个文件")
    parser.add_argument("--genre", default="戏腔", help="写入的流派，默认戏腔")
    parser.add_argument("--workers", type=int, default=4, help="并发上传数，默认 4")
    parser.add_argument("--limit", type=int, help="只导入前 N 首（用于试跑）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    args = parser.parse_args()

    if not config.oss_ready():
        print("OSS 未配置，请检查 .env 或环境变量")
        return 2

    files = collect(Path(args.source).expanduser(), args.limit)
    if not files:
        print(f"没有找到音频文件：{args.source}")
        return 1

    with SessionLocal() as db:
        used_ids = set(db.scalars(select(Song.id)).all())
        existing_audio = set(db.scalars(select(Song.audio)).all())
        next_order = int(db.scalar(select(func.coalesce(func.max(Song.added_order), -1))) or 0) + 1

        plans = []
        for path in files:
            number, title, artist = parse_name(path)
            base = base_song_id(path, number)
            # 先用稳定 ID 判断是否已导入，避免重跑时被当成新 ID 重复上传
            if f"audio/{base}{path.suffix.lower()}" in existing_audio:
                print(f"跳过  {path.name}（已入库）", flush=True)
                continue
            song_id = make_song_id(base, used_ids)
            key = f"audio/{song_id}{path.suffix.lower()}"
            lrc = path.with_suffix(".lrc")
            plans.append(
                {
                    "path": path,
                    "id": song_id,
                    "key": key,
                    "title": title or path.stem,
                    "artist": artist,
                    "duration": duration_of(path),
                    "lyrics": read_lrc(lrc) if lrc.exists() else [],
                    "order": next_order + len(plans),
                }
            )

        print(f"待导入 {len(plans)} 首，歌词 {sum(bool(p['lyrics']) for p in plans)} 份", flush=True)
        if args.dry_run:
            for item in plans[:10]:
                print(
                    f"计划  {item['id']} | {item['title']} / {item['artist']} "
                    f"/ {item['duration']}s / 歌词 {len(item['lyrics'])} 行 ← {item['path'].name}"
                )
            return 0

        total_lines = 0
        # 上面的 SELECT 已经开启事务，先结束它，避免与后面的显式事务冲突
        db.rollback()
        batch_size = max(1, args.workers * 2)
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for start in range(0, len(plans), batch_size):
                batch = plans[start : start + batch_size]
                results = list(
                    pool.map(lambda item: upload_one(item["path"], item["key"]), batch)
                )
                for item in batch:
                    db.add(
                        Song(
                            id=item["id"],
                            title=item["title"],
                            artist=item["artist"],
                            album="",
                            genre=args.genre,
                            duration=item["duration"],
                            cover="",
                            audio=item["key"],
                            added_order=item["order"],
                        )
                    )
                    db.flush()
                    for position, (second, text) in enumerate(item["lyrics"]):
                        db.add(
                            LyricLine(
                                song_id=item["id"],
                                position=position,
                                t=second,
                                text=text,
                            )
                        )
                    total_lines += len(item["lyrics"])
                db.commit()
                print(
                    f"进度  {min(start + len(batch), len(plans))}/{len(plans)}"
                    f"（{' '.join(dict.fromkeys(results))}）",
                    flush=True,
                )

    print(f"\n完成：新增 {len(plans)} 首，歌词 {total_lines} 行")

    # 资源是双写（OSS + 服务器 static）：本机导入后让服务器那份也补齐
    if not args.dry_run:
        from sync_server_assets import auto_sync

        auto_sync()
    return 0


if __name__ == "__main__":
    sys.exit(main())
