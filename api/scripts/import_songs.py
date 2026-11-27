#!/usr/bin/env python3
"""把本地音频上传到 OSS，并写入 songs 表。

用法：
    python scripts/import_songs.py --source /path/to/music          # 目录下所有音频
    python scripts/import_songs.py --source /path/to/song.mp3       # 单个文件
    python scripts/import_songs.py --source /path/to/song.mp3 --artist 张三 --title 晚风
    python scripts/import_songs.py --source /path/to/music --dry-run

约定：
- 元数据优先级：命令行参数 > 音频标签（装了 mutagen 时）> 文件名
  （"歌手 - 歌名.mp3" 会拆成歌手 / 歌名）；时长取标签，WAV 可用标准库兜底。
- 对象键为 audio/local-xxx.ext，song_id 为 local-xxx；已入库的同键歌曲跳过。
- 只写 songs 表，不动 data/seed/songs.json；如需重建库后保留，另行同步种子。
- OSS 配置复用 .env / 环境变量（OSS_ACCESS_KEY_ID / SECRET / BUCKET / ENDPOINT），
  上传逻辑复用 scripts/upload_assets.py，不额外安装依赖（mutagen 可选）。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from sqlalchemy import func, select  # noqa: E402

from app import config  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Song  # noqa: E402
from upload_assets import CONTENT_TYPES, remote_size, upload  # noqa: E402

AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def _first_text(tags: object, keys: tuple[str, ...]) -> str:
    """从 mutagen 的标签里取第一个非空文本（兼容 ID3 frame / MP4 列表值）。"""
    for key in keys:
        value = tags.get(key) if tags else None
        if value is None:
            continue
        if hasattr(value, "text"):
            value = value.text
        if isinstance(value, (list, tuple)):
            value = value[0] if value else ""
        text = str(value).strip()
        if text:
            return text
    return ""


def read_tags(path: Path) -> dict:
    """读取音频标签；未安装 mutagen 或解析失败时返回空字典，不中断导入。"""
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return {}
    try:
        audio = MutagenFile(path)
    except Exception:
        return {}
    if audio is None:
        return {}
    tags = audio.tags
    info = getattr(audio, "info", None)
    length = int(getattr(info, "length", 0) or 0)
    return {
        "title": _first_text(tags, ("TIT2", "title", "©nam")),
        "artist": _first_text(tags, ("TPE1", "artist", "©ART")),
        "album": _first_text(tags, ("TALB", "album", "©alb")),
        "genre": _first_text(tags, ("TCON", "genre", "©gen")),
        "duration": length,
    }


def wav_duration(path: Path) -> int:
    """WAV 用标准库读时长，避免没装 mutagen 时时长为 0。"""
    if path.suffix.lower() != ".wav":
        return 0
    import wave

    try:
        with wave.open(str(path), "rb") as wav:
            return int(wav.getnframes() / wav.getframerate())
    except (OSError, EOFError, ZeroDivisionError):
        return 0


def guess_from_name(path: Path) -> tuple[str, str]:
    """文件名兜底：'歌手 - 歌名.mp3' 拆成歌手 / 歌名。"""
    stem = re.sub(r"_+", " ", path.stem).strip()
    if " - " in stem:
        artist, title = (part.strip() for part in stem.split(" - ", 1))
        return title, artist
    return stem, ""


def make_song_id(path: Path, used_ids: set[str]) -> str:
    """生成与种子数据区分开的 song_id，并保证库内不冲突。"""
    raw = re.sub(r"[^A-Za-z0-9_-]+", "-", path.stem).strip("-").lower()
    if not raw:
        raw = hashlib.md5(path.name.encode("utf-8")).hexdigest()[:10]
    base = f"local-{raw[:40]}"
    candidate = base
    index = 2
    while candidate in used_ids:
        suffix = f"-{index}"
        candidate = f"{base[: 64 - len(suffix)]}{suffix}"
        index += 1
    used_ids.add(candidate)
    return candidate


def collect(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise SystemExit(f"文件或目录不存在：{source}")
    return [
        path
        for path in sorted(source.iterdir())
        if path.is_file()
        and not path.name.startswith("._")
        and path.suffix.lower() in AUDIO_SUFFIXES
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="上传本地音频到 OSS 并写入 songs 表")
    parser.add_argument("--source", required=True, help="本地音频文件或目录")
    parser.add_argument("--title", help="覆盖歌名（多文件时全部套用）")
    parser.add_argument("--artist", help="覆盖歌手（多文件时全部套用）")
    parser.add_argument("--album", help="覆盖专辑（多文件时全部套用）")
    parser.add_argument("--genre", help="覆盖流派（多文件时全部套用）")
    parser.add_argument("--duration", type=int, help="覆盖时长秒数（多文件时全部套用）")
    parser.add_argument("--dry-run", action="store_true", help="只打印导入计划，不上传、不入库")
    parser.add_argument("--force", action="store_true", help="远端已有同大小对象时仍重传")
    args = parser.parse_args()

    if not config.oss_ready():
        print("OSS 未配置，请检查 .env 或环境变量：OSS_ACCESS_KEY_ID / SECRET / BUCKET / ENDPOINT")
        return 2

    files = collect(Path(args.source).expanduser())
    files = [path for path in files if path.suffix.lower() in AUDIO_SUFFIXES]
    if not files:
        print(f"没有找到可导入的音频文件：{args.source}")
        return 1

    with SessionLocal() as db:
        used_ids = set(db.scalars(select(Song.id)).all())
        existing_audio = set(db.scalars(select(Song.audio)).all())
        next_order = int(db.scalar(select(func.coalesce(func.max(Song.added_order), -1))) or 0) + 1

        plans = []
        skipped = 0
        for path in files:
            tags = read_tags(path)
            name_title, name_artist = guess_from_name(path)
            song_id = make_song_id(path, used_ids)
            key = f"audio/{song_id}{path.suffix.lower()}"
            if key in existing_audio:
                skipped += 1
                print(f"跳过  {path.name}（{key} 已入库）")
                continue
            plans.append(
                {
                    "path": path,
                    "id": song_id,
                    "key": key,
                    "title": args.title or tags.get("title") or name_title or path.name,
                    "artist": args.artist or tags.get("artist") or name_artist,
                    "album": args.album or tags.get("album", ""),
                    "genre": args.genre or tags.get("genre", ""),
                    "duration": args.duration or tags.get("duration") or wav_duration(path),
                    "added_order": next_order + len(plans),
                }
            )

        print(f"待导入 {len(plans)} 首，已入库跳过 {skipped} 首", flush=True)
        if args.dry_run:
            for item in plans:
                print(
                    f"计划  {item['key']} <- {item['path']}"
                    f" | {item['title']} / {item['artist']} / {item['duration']}s"
                )
            return 0

        inserted = 0
        for item in plans:
            data = item["path"].read_bytes()
            if not args.force and remote_size(item["key"]) == len(data):
                print(f"复用  {item['key']}（远端已有，{len(data)} 字节）")
            else:
                upload(item["key"], data, CONTENT_TYPES[item["path"].suffix.lower()])
                print(f"上传  {item['key']}（{len(data)} 字节）")
            db.add(
                Song(
                    id=item["id"],
                    title=item["title"],
                    artist=item["artist"],
                    album=item["album"],
                    genre=item["genre"],
                    duration=item["duration"],
                    audio=item["key"],
                    added_order=item["added_order"],
                )
            )
            inserted += 1
        db.commit()

    print(f"\n完成：上传/入库 {inserted} 首，已入库跳过 {skipped} 首，共 {len(files)} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
