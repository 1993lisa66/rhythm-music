#!/usr/bin/env python3
"""把 static/covers 下的封面同步到阿里云 OSS（增量：同名同大小跳过）。

用法：
    python scripts/upload_covers.py             # 增量上传
    python scripts/upload_covers.py --dry-run   # 只打印将要上传的文件
    python scripts/upload_covers.py --force     # 全部重传

依赖：只用标准库（urllib + hmac + hashlib），不需要安装 oss2。
配置：项目根目录 .env 或环境变量
    OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / OSS_BUCKET / OSS_ENDPOINT
可选：
    OSS_PUBLIC_BASE  自定义域名 / CDN；不填则用 https://<bucket>.<endpoint>
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import sys
import urllib.error
import urllib.request
from email.utils import formatdate
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import config  # noqa: E402  （必须在 sys.path 调整之后导入）

CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _sign(method: str, content_md5: str, content_type: str, date: str, resource: str) -> str:
    """OSS V1 签名：HMAC-SHA1(Base64)。"""
    string_to_sign = f"{method}\n{content_md5}\n{content_type}\n{date}\n{resource}"
    digest = hmac.new(
        config.OSS_ACCESS_KEY_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _request(method: str, key: str, body: bytes | None = None, content_type: str = ""):
    """对 <bucket>.<endpoint>/<key> 发签名请求，返回 (status, headers)。"""
    bucket = config.OSS_BUCKET
    endpoint = config.OSS_ENDPOINT.replace("https://", "").replace("http://", "").strip("/")
    url = f"https://{bucket}.{endpoint}/{key}"
    date = formatdate(usegmt=True)
    content_md5 = base64.b64encode(hashlib.md5(body).digest()).decode() if body else ""
    signature = _sign(method, content_md5, content_type, date, f"/{bucket}/{key}")

    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Date", date)
    request.add_header("Authorization", f"OSS {config.OSS_ACCESS_KEY_ID}:{signature}")
    if content_md5:
        request.add_header("Content-MD5", content_md5)
    if content_type:
        request.add_header("Content-Type", content_type)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.headers
    except urllib.error.URLError as error:
        raise SystemExit(f"无法连接 OSS（{endpoint}）：{error.reason}") from error


def remote_size(key: str) -> int | None:
    """返回远端对象大小；不存在返回 None。"""
    status, headers = _request("HEAD", key)
    if status == 200:
        return int(headers.get("Content-Length") or 0)
    if status == 404:
        return None
    raise SystemExit(f"HEAD {key} 失败：HTTP {status}")


def upload(key: str, data: bytes, content_type: str) -> None:
    status, _ = _request("PUT", key, body=data, content_type=content_type)
    if status != 200:
        raise SystemExit(f"PUT {key} 失败：HTTP {status}")


def public_url(key: str) -> str:
    base = config.OSS_PUBLIC_BASE.rstrip("/")
    if base:
        return f"{base}/{key}"
    endpoint = config.OSS_ENDPOINT.replace("https://", "").replace("http://", "").strip("/")
    return f"https://{config.OSS_BUCKET}.{endpoint}/{key}"


def main() -> int:
    parser = argparse.ArgumentParser(description="同步封面到阿里云 OSS")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不实际上传")
    parser.add_argument("--force", action="store_true", help="忽略远端大小，全部重传")
    parser.add_argument(
        "--prefix",
        default="covers",
        help="对象前缀，默认 covers（即 OSS 上 /covers/xxx.jpg）",
    )
    args = parser.parse_args()

    if not config.oss_ready():
        missing = [
            name
            for name, value in (
                ("OSS_ACCESS_KEY_ID", config.OSS_ACCESS_KEY_ID),
                ("OSS_ACCESS_KEY_SECRET", config.OSS_ACCESS_KEY_SECRET),
                ("OSS_BUCKET", config.OSS_BUCKET),
                ("OSS_ENDPOINT", config.OSS_ENDPOINT),
            )
            if not value
        ]
        print(f"OSS 未配置，缺少：{', '.join(missing)}")
        return 2

    files = sorted(p for p in config.COVER_DIR.iterdir() if p.is_file())
    if not files:
        print(f"没有找到封面文件：{config.COVER_DIR}")
        return 1

    uploaded = skipped = 0
    for path in files:
        key = f"{args.prefix.strip('/')}/{path.name}"
        data = path.read_bytes()
        size = len(data)
        exists = None if args.force else remote_size(key)
        if exists == size:
            skipped += 1
            print(f"跳过  {key}（远端已有，{size} 字节）")
            continue
        if args.dry_run:
            print(f"待传  {key}（{size} 字节）")
            continue
        upload(key, data, CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"))
        uploaded += 1
        print(f"上传  {key}（{size} 字节）")

    print(f"\n完成：上传 {uploaded}，跳过 {skipped}，共 {len(files)} 个文件")
    print(f"公共地址示例：{public_url(f'{args.prefix}/' + files[0].name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
