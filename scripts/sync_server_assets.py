#!/usr/bin/env python3
"""让服务器本地的静态资源与 OSS 对齐（在服务器上执行 sync_assets_local.py）。

为什么需要它：
    资源是「双写」的 —— 每个音频/封面既在 OSS，也在服务器 static/ 下。
    导入脚本在开发机上跑时，upload() 只能写到「本机 static + OSS」，
    服务器那份还缺，所以上传结束后调用本脚本，让服务器补齐。

用法：
    DEPLOY_PASSWORD=*** python scripts/sync_server_assets.py
    python scripts/sync_server_assets.py --dry-run

没有配置密码时直接跳过（不阻塞导入流程）。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

REMOTE_APP_DIR = "/www/wwwroot/rhythm-music-api"
REMOTE_VENV = "/www/server/pyporject_evn/rhythm-music-api"


def sync_server(host: str, user: str, password: str, port: int, dry_run: bool = False) -> bool:
    """在服务器上跑一次增量同步；返回是否成功。"""
    from deploy import Remote  # 复用部署脚本的 SSH/SCP 封装

    flag = " --dry-run" if dry_run else " --workers 4"
    command = (
        f"cd {REMOTE_APP_DIR} && "
        f"{REMOTE_VENV}/bin/python scripts/sync_assets_local.py{flag}"
    )
    remote = Remote(host, user, password, port)
    try:
        remote.run(command)
        return True
    except SystemExit as error:  # Remote.run 失败会 SystemExit
        print(f"[assets] 服务器同步失败：{error}")
        return False
    finally:
        remote.close()


def auto_sync(quiet: bool = False) -> bool:
    """导入脚本收尾时调用：有密码就同步，没密码就跳过。"""
    password = os.getenv("DEPLOY_PASSWORD") or os.getenv("SSHPASS")
    if not password:
        if not quiet:
            print("[assets] 未设置 DEPLOY_PASSWORD，跳过服务器同步（可稍后手动执行本脚本）")
        return False
    host = os.getenv("DEPLOY_HOST", "8.141.121.203")
    user = os.getenv("DEPLOY_USER", "root")
    port = int(os.getenv("DEPLOY_PORT", "22"))
    return sync_server(host, user, password, port)


def main() -> int:
    parser = argparse.ArgumentParser(description="把新上传的资源补到服务器本地静态目录")
    parser.add_argument("--host", default=os.getenv("DEPLOY_HOST", "8.141.121.203"))
    parser.add_argument("--user", default=os.getenv("DEPLOY_USER", "root"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DEPLOY_PORT", "22")))
    parser.add_argument("--password", default=os.getenv("DEPLOY_PASSWORD") or os.getenv("SSHPASS"))
    parser.add_argument("--dry-run", action="store_true", help="只统计，不下载")
    args = parser.parse_args()

    if not args.password:
        print("缺少密码：设置 DEPLOY_PASSWORD 环境变量或用 --password 传入")
        return 2
    return 0 if sync_server(args.host, args.user, args.password, args.port, args.dry_run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
