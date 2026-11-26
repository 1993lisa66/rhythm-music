#!/usr/bin/env python3
"""一键部署 rhythm 前端 + 后端到宝塔服务器。

流程：
1. 本地构建前端（npm install / npm run build）；
2. 打包后端代码、前端 dist、初始数据库；
3. 通过 SSH/SCP 上传到服务器；
4. 在服务器上创建 /www/wwwroot 目录、安装 Python 3.11、建虚拟环境；
5. 用宝塔自身的 Python 项目模型创建/重启后端项目，用宝塔站点模型创建前端站点；
6. 写入 Nginx 反代配置并校验 /health 与首页。

用法：
    export DEPLOY_PASSWORD='服务器密码'
    python scripts/deploy.py
    python scripts/deploy.py --skip-build          # 前端 dist 已是最新时
    python scripts/deploy.py --password '***'      # 不推荐，会出现在 shell 历史

依赖：本机有 ssh / scp，以及 sshpass 或 expect 之一（macOS 自带 expect）。
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FRONTEND = BASE_DIR.parent / "rhythm-music-app"

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
SKIP_SUFFIXES = (".pyc", ".bak", ".bak-20261127")


def log(message: str) -> None:
    print(f"[deploy] {message}", flush=True)


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    printable = " ".join(cmd)
    log(f"$ {printable}")
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


class Remote:
    """用 sshpass（优先）或 expect 执行 SSH/SCP，密码只放环境变量。"""

    def __init__(self, host: str, user: str, password: str, port: int = 22) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.sshpass = shutil.which("sshpass")
        self.expect = shutil.which("expect")
        if not self.sshpass and not self.expect:
            raise SystemExit("需要安装 sshpass 或 expect 才能非交互登录服务器")
        self.tmp = tempfile.TemporaryDirectory(prefix="rhythm-ssh-")
        self.expect_ssh = Path(self.tmp.name) / "ssh.exp"
        self.expect_scp = Path(self.tmp.name) / "scp.exp"
        if not self.sshpass:
            self._write_expect_scripts()

    def _write_expect_scripts(self) -> None:
        ssh_script = """#!/usr/bin/expect -f
set timeout 900
set host [lindex $argv 0]
set user [lindex $argv 1]
set cmd [lindex $argv 2]
set pw $env(SSHPASS)
log_user 1
spawn ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR $user@$host $cmd
expect {
    -re {(?i)password:} { send -- "$pw\\r"; exp_continue }
    -re {(?i)yes/no} { send -- "yes\\r"; exp_continue }
    eof
}
set result [wait]
exit [lindex $result 3]
"""
        scp_script = """#!/usr/bin/expect -f
set timeout 900
set host [lindex $argv 0]
set user [lindex $argv 1]
set src [lindex $argv 2]
set dst [lindex $argv 3]
set pw $env(SSHPASS)
log_user 1
spawn scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR $src $user@$host:$dst
expect {
    -re {(?i)password:} { send -- "$pw\\r"; exp_continue }
    -re {(?i)yes/no} { send -- "yes\\r"; exp_continue }
    eof
}
set result [wait]
exit [lindex $result 3]
"""
        self.expect_ssh.write_text(ssh_script)
        self.expect_scp.write_text(scp_script)
        self.expect_ssh.chmod(0o700)
        self.expect_scp.chmod(0o700)

    def _env(self) -> dict:
        env = os.environ.copy()
        env["SSHPASS"] = self.password
        return env

    def run(self, command: str) -> None:
        if self.sshpass:
            cmd = [
                self.sshpass,
                "-e",
                "ssh",
                "-p",
                str(self.port),
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "LogLevel=ERROR",
                f"{self.user}@{self.host}",
                command,
            ]
            subprocess.run(cmd, env=self._env(), check=True)
        else:
            run([str(self.expect_ssh), self.host, self.user, command], env=self._env())

    def upload(self, local: Path, remote: str) -> None:
        if self.sshpass:
            cmd = [
                self.sshpass,
                "-e",
                "scp",
                "-P",
                str(self.port),
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "LogLevel=ERROR",
                str(local),
                f"{self.user}@{self.host}:{remote}",
            ]
            subprocess.run(cmd, env=self._env(), check=True)
        else:
            run(
                [str(self.expect_scp), self.host, self.user, str(local), remote],
                env=self._env(),
            )

    def close(self) -> None:
        self.tmp.cleanup()


def build_frontend(frontend: Path, skip: bool) -> None:
    if skip:
        log("跳过前端构建")
        return
    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("未找到 npm，请先安装 Node.js")
    if not (frontend / "package.json").exists():
        raise SystemExit(f"前端目录不正确：{frontend}")
    if not (frontend / "node_modules").exists():
        run([npm, "install"], cwd=frontend)
    run([npm, "run", "build"], cwd=frontend)
    if not (frontend / "dist" / "index.html").exists():
        raise SystemExit("前端构建完成但没有 dist/index.html")


def add_tree(tar: tarfile.TarFile, root: Path, skip: set[str]) -> None:
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name.startswith((".DS_Store", "._")) or path.name.endswith(SKIP_SUFFIXES):
            continue
        if path.name == "rhythm.db":
            continue
        if path.is_file():
            tar.add(path, arcname=str(rel))


def package(staging: Path, frontend: Path) -> Path:
    api_tgz = staging / "api.tgz"
    with tarfile.open(api_tgz, "w:gz") as tar:
        add_tree(tar, BASE_DIR, SKIP_DIRS)

    web_tgz = staging / "web.tgz"
    dist = frontend / "dist"
    if not (dist / "index.html").exists():
        raise SystemExit(f"找不到前端构建产物：{dist}")
    with tarfile.open(web_tgz, "w:gz") as tar:
        for path in sorted(dist.rglob("*")):
            if path.is_file():
                tar.add(path, arcname=str(path.relative_to(dist)))

    db_tgz = staging / "db.tgz"
    db_file = BASE_DIR / "rhythm.db"
    if db_file.exists():
        with tarfile.open(db_tgz, "w:gz") as tar:
            tar.add(db_file, arcname="rhythm.db")

    for name in ("deploy_remote.sh", "baota_ensure.py"):
        shutil.copy2(BASE_DIR / "scripts" / name, staging / name)

    bundle = staging / "bundle.tgz"
    with tarfile.open(bundle, "w:gz") as tar:
        for path in sorted(staging.iterdir()):
            if path != bundle:
                tar.add(path, arcname=path.name)
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="部署 rhythm 前端与后端到宝塔服务器")
    parser.add_argument("--host", default="8.141.121.203")
    parser.add_argument("--user", default="root")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--password", default=os.getenv("DEPLOY_PASSWORD"))
    parser.add_argument("--frontend-dir", type=Path, default=DEFAULT_FRONTEND)
    parser.add_argument("--skip-build", action="store_true", help="跳过 npm run build")
    parser.add_argument("--keep-remote", action="store_true", help="保留服务器上的临时包")
    args = parser.parse_args()

    password = args.password or getpass.getpass("服务器 SSH 密码：")
    frontend = args.frontend_dir.expanduser().resolve()
    build_frontend(frontend, args.skip_build)

    staging = Path(tempfile.mkdtemp(prefix="rhythm-deploy-"))
    try:
        bundle = package(staging, frontend)
        size_mb = bundle.stat().st_size / 1024 / 1024
        log(f"部署包已生成：{bundle}（{size_mb:.1f} MB）")

        remote = Remote(args.host, args.user, password, args.port)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        remote_dir = f"/tmp/rhythm-deploy-{stamp}"
        try:
            remote.run(f"rm -rf {remote_dir} && mkdir -p {remote_dir}")
            remote.upload(bundle, f"{remote_dir}/bundle.tgz")
            remote.run(
                f"tar -xzf {remote_dir}/bundle.tgz -C {remote_dir} && "
                f"DEPLOY_HOST={args.host} bash {remote_dir}/deploy_remote.sh {remote_dir}"
            )
            if not args.keep_remote:
                remote.run(f"rm -rf {remote_dir}")
        finally:
            remote.close()
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    log(json.dumps({"status": "ok", "frontend": "http://8.141.121.203/", "api": "http://8.141.121.203/api/v1/songs"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
