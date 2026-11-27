#!/usr/bin/env python3
"""在宝塔面板里确保 Python 项目与静态站点存在（供 deploy_remote.sh 调用）。

用法（必须用宝塔自带解释器运行）：
    /www/server/panel/pyenv/bin/python3 baota_ensure.py env
    /www/server/panel/pyenv/bin/python3 baota_ensure.py project
    /www/server/panel/pyenv/bin/python3 baota_ensure.py site

说明：
- 直接调用宝塔自身的 projectModel / panelSite 类，等价于在面板里点「Python 项目 / 网站」；
- 项目已存在时只重启，不重复创建；站点已存在时跳过 AddSite，保留面板里的绑定关系；
- Nginx 反向代理配置由 deploy_remote.sh 覆盖写入，保证 SPA 与 /api、/covers 可用。
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "/www/server/panel/class")

import public  # noqa: E402

PROJECT_NAME = "rhythm-music-api"
SITE_DOMAIN = "rhythm.local"
APP_DIR = "/www/wwwroot/rhythm-music-api"
VENV_DIR = "/www/server/pyporject_evn/rhythm-music-api"
VENV_PYTHON = f"{VENV_DIR}/bin/python"
UVICORN = f"{VENV_DIR}/bin/uvicorn"


def ensure_env() -> None:
    from mod.project.python.pyenv_tool import EnvironmentManager

    manager = EnvironmentManager()
    if manager.get_env_py_path(VENV_PYTHON):
        print(f"[baota] Python 环境已存在：{VENV_DIR}")
        return
    result = manager.add_python_env("venv", VENV_DIR)
    print(f"[baota] 登记 Python 环境：{result or 'ok'}")


def ensure_project() -> None:
    from projectModel.pythonModel import main

    model = main()
    exists = public.M("sites").where(
        "name=? and project_type=?", (PROJECT_NAME, "Python")
    ).count()
    if exists:
        result = model.RestartProject(public.to_dict_obj({"name": PROJECT_NAME}))
        print(f"[baota] 重启 Python 项目：{json.dumps(result, ensure_ascii=False)}")
        return

    get = public.to_dict_obj(
        {
            "pjname": PROJECT_NAME,
            "port": "8000",
            "stype": "command",
            "path": APP_DIR,
            "python_bin": VENV_PYTHON,
            "requirement_path": f"{APP_DIR}/requirements.txt",
            "project_cmd": f"{UVICORN} app.main:app --host 127.0.0.1 --port 8000",
            "framework": "python",
            "auto_run": "1",
            "user": "root",
        }
    )
    result = model.CreateProject(get)
    print(f"[baota] 创建 Python 项目：{json.dumps(result, ensure_ascii=False)}")


def ensure_site() -> None:
    from panelSite import panelSite

    exists = public.M("sites").where("name=?", (SITE_DOMAIN,)).count()
    if exists:
        print(f"[baota] 站点已存在：{SITE_DOMAIN}")
        return

    get = public.to_dict_obj(
        {
            "path": "/www/wwwroot/rhythm-music-app/dist",
            "port": "80",
            "ps": "rhythm-music-app",
            "type_id": "0",
            "project_type": "PHP",
            "version": "00",
            "webname": json.dumps(
                {"domain": SITE_DOMAIN, "domainlist": [SITE_DOMAIN], "count": 1}
            ),
            "ftp": "false",
            "sql": "false",
        }
    )
    result = panelSite().AddSite(get)
    print(f"[baota] 创建静态站点：{json.dumps(result, ensure_ascii=False, default=str)}")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("env", "project", "site"):
        print("用法：baota_ensure.py env|project|site")
        return 2
    {"env": ensure_env, "project": ensure_project, "site": ensure_site}[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
