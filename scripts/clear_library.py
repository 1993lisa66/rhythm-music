#!/usr/bin/env python3
"""清空曲库：删除 OSS 上的歌曲资源，并清空 songs 及其关联记录。

默认行为：
  - 删除 OSS 上 audio/ 下的全部对象（歌曲音频）；
  - 删除 OSS 上 covers/ 下「只被歌曲引用、未被歌单/文案块引用」的封面；
  - 清空 songs 及依赖它的表（歌词 / 收藏 / 播放记录 / 队列 / 歌单曲目）。

用法：
    python scripts/clear_library.py --dry-run     # 只统计，不删除
    python scripts/clear_library.py --yes         # 执行（会先备份数据库）
    python scripts/clear_library.py --yes --keep-oss   # 只清数据库，保留 OSS 文件
    python scripts/clear_library.py --yes --keep-db    # 只删 OSS 文件，保留数据库

依赖：只用标准库（urllib + hmac + hashlib），与 scripts/upload_assets.py 一致。
注意：清空后必须让服务以 RHYTHM_AUTO_SEED=0 运行，否则重启会自动灌回内置曲库。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import re
import shutil
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import formatdate
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import config  # noqa: E402

# 依赖 songs 的表，按「先删子表」的顺序排列
DEPENDENT_TABLES = (
    "favorites",
    "play_events",
    "queue_items",
    "playlist_tracks",
    "lyric_lines",
)
COVER_REF_RE = re.compile(r"covers/[A-Za-z0-9_.\-]+")


def _endpoint_base() -> str:
    endpoint = config.OSS_ENDPOINT.replace("https://", "").replace("http://", "").strip("/")
    return f"https://{config.OSS_BUCKET}.{endpoint}"


def _call(method: str, key: str = "", params: str = "", body: bytes | None = None):
    """对 <bucket>.<endpoint> 发 V1 签名请求，返回 (status, body)。"""
    path = f"/{key}" if key else "/"
    url = f"{_endpoint_base()}{path}" + (f"?{params}" if params else "")
    date = formatdate(usegmt=True)
    content_md5 = base64.b64encode(hashlib.md5(body).digest()).decode() if body else ""
    string_to_sign = f"{method}\n{content_md5}\n\n{date}\n/{config.OSS_BUCKET}{path}"
    signature = base64.b64encode(
        hmac.new(
            config.OSS_ACCESS_KEY_SECRET.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")

    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Date", date)
    request.add_header("Authorization", f"OSS {config.OSS_ACCESS_KEY_ID}:{signature}")
    if content_md5:
        request.add_header("Content-MD5", content_md5)

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except urllib.error.URLError as error:
        raise SystemExit(f"无法连接 OSS（{_endpoint_base()}）：{error.reason}") from error


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def list_objects(prefix: str) -> list[str]:
    """列出指定前缀下的全部对象键（分页取完）。"""
    keys: list[str] = []
    marker = ""
    while True:
        params = f"prefix={urllib.parse.quote(prefix, safe='')}&max-keys=1000"
        if marker:
            params += f"&marker={urllib.parse.quote(marker, safe='')}"
        status, body = _call("GET", params=params)
        if status != 200:
            raise SystemExit(f"列取 OSS 失败：HTTP {status} {body[:200]!r}")

        root = ET.fromstring(body)
        page = [child.text for child in root.iter() if _local_name(child.tag) == "Key" and child.text]
        keys.extend(page)

        truncated = next(
            (child.text for child in root.iter() if _local_name(child.tag) == "IsTruncated"), "false"
        )
        if str(truncated).lower() != "true" or not page:
            break
        marker = page[-1]
    return keys


def delete_object(key: str) -> tuple[str, bool, str]:
    status, body = _call("DELETE", key)
    if status in (200, 204):
        return key, True, ""
    return key, False, f"HTTP {status} {body[:120]!r}"


def parse_db_path() -> Path:
    url = config.DATABASE_URL
    if not url.startswith("sqlite:///"):
        raise SystemExit(f"只支持 sqlite 数据库，当前为：{url}")
    return Path(url[len("sqlite:///") :])


def normalize_cover(value: str) -> str:
    key = (value or "").strip().lstrip("/")
    if not key:
        return ""
    return key if key.startswith("covers/") else f"covers/{key}"


def protected_covers(db: sqlite3.Connection) -> set[str]:
    """歌单封面、用户头像、文案块里引用到的封面都要保留。"""
    keep: set[str] = set()

    for (value,) in db.execute("select distinct cover from playlists where cover != ''"):
        keep.add(normalize_cover(value))
    for (value,) in db.execute("select distinct avatar from users where avatar != ''"):
        keep.add(normalize_cover(value))
    for (payload,) in db.execute("select payload from content_blocks"):
        keep.update(f"covers/{name}" for name in COVER_REF_RE.findall(payload or ""))
    return {key for key in keep if key}


def table_count(db: sqlite3.Connection, table: str) -> int:
    try:
        return db.execute(f"select count(*) from {table}").fetchone()[0]
    except sqlite3.Error:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="清空曲库：删除 OSS 歌曲资源并清空 songs 表")
    parser.add_argument("--dry-run", action="store_true", help="只统计计划，不删除")
    parser.add_argument("--yes", action="store_true", help="确认执行删除（不加则只打印计划）")
    parser.add_argument("--keep-oss", action="store_true", help="跳过 OSS 删除，只清数据库")
    parser.add_argument("--keep-db", action="store_true", help="跳过数据库清理，只删 OSS 文件")
    parser.add_argument("--workers", type=int, default=8, help="并发删除线程数，默认 8")
    args = parser.parse_args()

    db_path = parse_db_path()
    if not db_path.exists():
        raise SystemExit(f"数据库不存在：{db_path}")
    db = sqlite3.connect(db_path)

    print(f"数据库：{db_path}")
    for table in ("songs", *DEPENDENT_TABLES, "playlists", "users"):
        print(f"  {table:16s} {table_count(db, table)}")

    keep = protected_covers(db)
    song_covers = {
        normalize_cover(row[0])
        for row in db.execute("select distinct cover from songs where cover != ''")
    }

    audio_keys: list[str] = []
    cover_keys: list[str] = []
    if config.oss_ready() and not args.keep_oss:
        print(f"\nOSS：{_endpoint_base()}")
        audio_keys = list_objects("audio/")
        all_covers = list_objects("covers/")
        cover_keys = [key for key in all_covers if key not in keep]
        print(f"  audio/ 对象 {len(audio_keys)} 个（全部删除）")
        print(f"  covers/ 对象 {len(all_covers)} 个，保留 {len(all_covers) - len(cover_keys)} 个（歌单等在用），删除 {len(cover_keys)} 个")
        if song_covers & keep:
            print(f"  其中 {len(song_covers & keep)} 个歌曲封面被歌单复用，已保留")
    elif not args.keep_oss:
        print("\nOSS 未配置，跳过文件删除")
        args.keep_oss = True

    if args.dry_run or not args.yes:
        print("\n（预览模式，未做任何删除；确认后加 --yes 执行）")
        return 0

    backup = None
    if not args.keep_db:
        backup_dir = db_path.parent / "data" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{db_path.stem}-{datetime.now():%Y%m%d-%H%M%S}.db"
        shutil.copy2(db_path, backup)
        print(f"\n已备份数据库：{backup}")

    failures: list[tuple[str, str]] = []
    if not args.keep_oss and (audio_keys or cover_keys):
        targets = audio_keys + cover_keys
        print(f"开始删除 {len(targets)} 个 OSS 对象…")
        done = 0
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for key, ok, error in pool.map(delete_object, targets):
                done += 1
                if not ok:
                    failures.append((key, error))
                if done % 100 == 0:
                    print(f"  已处理 {done}/{len(targets)}")
        print(f"OSS 删除完成：成功 {len(targets) - len(failures)}，失败 {len(failures)}")
        for key, error in failures[:10]:
            print(f"  失败 {key}：{error}")

    if not args.keep_db:
        # index 是 SQL 保留字，必须加引号；这个更新失败不应该让整笔删除回滚
        with db:
            for table in DEPENDENT_TABLES:
                db.execute(f"delete from {table}")
            removed = db.execute("delete from songs").rowcount
        try:
            with db:
                db.execute('update player_state set "index" = 0, position = 0, playing = 0')
        except sqlite3.Error as error:
            print(f"重置播放进度失败（不影响曲库清空）：{error}")
        print(f"数据库清理完成：删除 {removed} 首歌曲及相关记录")

    print("\n完成。若服务仍在运行，请重启并确保以 RHYTHM_AUTO_SEED=0 启动，否则会自动灌回内置曲库。")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
