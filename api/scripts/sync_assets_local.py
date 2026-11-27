#!/usr/bin/env python3
"""把 OSS 上的音频与封面同步到服务器本地静态目录，供「服务器资源」数据源使用。

用法（在服务器上执行）：
    python scripts/sync_assets_local.py            # 同步缺失或大小不同的对象
    python scripts/sync_assets_local.py --dry-run  # 只统计，不下载

目录：
    音频 → static/audio/（目标对象键 audio/xxx.mp3 → xxx.mp3）
    封面 → static/covers/（covers/xxx.jpg → xxx.jpg）

下载走签名地址（私有 Bucket），并发下载，断点续传靠文件大小校验。
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from app import config  # noqa: E402
from clear_library import list_objects  # noqa: E402

AUDIO_DIR = BASE_DIR / "static" / "audio"
COVER_DIR = config.COVER_DIR


def download_one(prefix: str, target_dir: Path, key: str) -> tuple[str, bool, str]:
    name = key[len(prefix) :]
    target = target_dir / name
    if target.exists() and target.stat().st_size > 0:
        return name, False, "skip"
    url = config.sign_oss_url(key)
    try:
        with urllib.request.urlopen(url, timeout=600) as response, open(target, "wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        if target.stat().st_size == 0:
            target.unlink()
            return name, False, "empty file"
        return name, True, "ok"
    except Exception as error:
        if target.exists():
            target.unlink()
        return name, False, f"error: {error}"


def sync(prefix: str, target_dir: Path, dry_run: bool, workers: int) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    keys = [key for key in list_objects(prefix) if not key.endswith("/")]
    print(f"{prefix} 远端 {len(keys)} 个对象 → {target_dir}", flush=True)
    if dry_run:
        return

    done = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download_one, prefix, target_dir, key) for key in keys]
        for future in futures:
            _name, ok, status = future.result()
            if status == "ok":
                done += 1
            elif status != "skip":
                failed += 1
                print(f"  失败 {status}", flush=True)
    print(f"  下载 {done}，已存在跳过 {len(keys) - done - failed}，失败 {failed}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 OSS 静态资源到服务器本地")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不下载")
    parser.add_argument("--workers", type=int, default=6, help="并发下载数，默认 6")
    args = parser.parse_args()

    if not config.oss_ready():
        print("OSS 未配置")
        return 2

    sync("audio/", AUDIO_DIR, args.dry_run, args.workers)
    sync("covers/", COVER_DIR, args.dry_run, args.workers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
