#!/bin/bash
# 服务器端部署脚本，由 deploy.py 上传后在目标机执行。
# 参数：$1 = 本次上传包所在目录（含 api.tgz / web.tgz / db.tgz / baota_ensure.py）
set -euo pipefail

PKG_DIR="${1:?缺少部署包目录}"
DEPLOY_HOST="${DEPLOY_HOST:-8.141.121.203}"
APP_DIR="/www/wwwroot/rhythm-music-api"
WEB_DIR="/www/wwwroot/rhythm-music-app"
VENV_DIR="/www/server/pyporject_evn/rhythm-music-api"
PANEL_DIR="/www/server/panel"
SITE_CONF="${PANEL_DIR}/vhost/nginx/rhythm.local.conf"

echo "[1/6] 创建目录"
mkdir -p "${APP_DIR}" "${WEB_DIR}/dist" /www/backup/rhythm /www/wwwlogs

echo "[2/6] 解包后端与前端"
tar -xzf "${PKG_DIR}/api.tgz" -C "${APP_DIR}"
if [ -f "${PKG_DIR}/db.tgz" ] && [ ! -f "${APP_DIR}/rhythm.db" ]; then
    tar -xzf "${PKG_DIR}/db.tgz" -C "${APP_DIR}"
    echo "       首次部署，已放入初始 rhythm.db"
fi
# 宝塔建站会给站点目录加 .user.ini 并 chattr +i，先解锁再替换
chattr -i "${WEB_DIR}/dist/.user.ini" 2>/dev/null || true
rm -rf "${WEB_DIR}/dist"
mkdir -p "${WEB_DIR}/dist"
tar -xzf "${PKG_DIR}/web.tgz" -C "${WEB_DIR}/dist"

echo "[3/6] 准备 Python 3.11 与虚拟环境"
if ! command -v python3.11 >/dev/null 2>&1; then
    yum install -y python3.11 >/tmp/rhythm-yum-py311.log 2>&1
fi
if ! python3.11 -m pip -V >/dev/null 2>&1; then
    yum install -y python3.11-pip >/tmp/rhythm-yum-pip.log 2>&1
fi
if [ ! -x "${VENV_DIR}/bin/python" ]; then
    python3.11 -m venv "${VENV_DIR}"
fi
"${VENV_DIR}/bin/pip" install -q -U pip
"${VENV_DIR}/bin/pip" install -q -r "${APP_DIR}/requirements.txt"

echo "[4/6] 登记宝塔 Python 项目与静态站点"
cd "${PANEL_DIR}"
./pyenv/bin/python3 "${PKG_DIR}/baota_ensure.py" env
./pyenv/bin/python3 "${PKG_DIR}/baota_ensure.py" project
./pyenv/bin/python3 "${PKG_DIR}/baota_ensure.py" site

echo "[5/6] 写入 Nginx 配置"
cat > "${SITE_CONF}" <<'NGINX'
server {
    listen 80;
    server_name 8.141.121.203 rhythm.local;

    root /www/wwwroot/rhythm-music-app/dist;
    index index.html;

    access_log /www/wwwlogs/rhythm-music-app.log;
    error_log /www/wwwlogs/rhythm-music-app.error.log;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /covers/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /assets/ {
        expires 12h;
        try_files $uri =404;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX
sed -i "s/8.141.121.203/${DEPLOY_HOST}/g" "${SITE_CONF}"
nginx -t
nginx -s reload

echo "[6/6] 等待后端就绪"
for _ in $(seq 1 40); do
    if curl -sf --max-time 3 http://127.0.0.1:8000/health >/dev/null; then
        echo "       后端已就绪"
        break
    fi
    sleep 3
done
curl -sS --max-time 5 http://127.0.0.1:8000/health || {
    echo "       后端未就绪，最近日志："
    tail -40 /www/server/python_project/vhost/logs/rhythm-music-api.log 2>/dev/null || true
    exit 1
}
echo
echo "前端：http://${DEPLOY_HOST}/"
echo "接口：http://${DEPLOY_HOST}/api/v1/songs"
