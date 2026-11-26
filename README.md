# 韵律音乐 App · Python API

依据 `韵律音乐App-开发文档.md` 与前端 `rhythm-music-app` 的实际数据需求实现的 REST 接口。
响应字段与前端 `src/data/*.json` 一一对应（snake_case → camelCase），前端接入时字段名无需改动。

## 技术栈

FastAPI 0.165 · SQLAlchemy 2.1 · SQLite · Pydantic 2.14 · Python 3.14

## 启动

```bash
cd rhythm-music-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health
- 封面静态文件：`/covers/cover_1.jpg`

首次启动自动建表并从 `data/seed/*.json` 灌入初始数据；`rhythm.db` 删掉即还原。

```bash
.venv/bin/python -m app.seed --reset   # 手动重建数据
```

## 目录

```
app/
  config.py     环境变量与常量
  db.py         引擎 / 会话
  models.py     ORM（内容表 + 用户状态表分离）
  schemas.py    请求 / 响应模型（camelCase 输出）
  services.py   序列化、播放器状态机、设置读写
  seed.py       初始化数据
  main.py       入口 / CORS / 统一错误
  routers/      songs playlists browse search player favorites recent downloads me
data/seed/      从前端复制过来的初始 JSON
static/covers/  24 张封面
```

## 接口一览（前缀 `/api/v1`）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/songs` | 列表，支持 `q` `genre` `liked` `sort` `order` `limit` `offset` |
| GET | `/songs/{id}` | 单曲详情 |
| GET | `/songs/{id}/lyrics` | 带时间轴歌词 |
| GET | `/genres` | 流派及曲目数 |
| GET | `/playlists` | 歌单列表，`ids=a,b` 过滤 |
| GET | `/playlists/{id}` | 歌单详情含曲目 |
| POST | `/playlists/{id}/play` | 播放全部（可传 `songId` 指定起始曲） |
| POST | `/playlists/{id}/shuffle` | 随机播放 |
| GET | `/discover` | 发现页聚合（问候语 / 精选 / 随心听 / 最近播放） |
| GET | `/library` | 乐库聚合（Tabs / 最近添加 / 我的歌单） |
| GET | `/library/albums` | 专辑视图（按专辑聚合） |
| GET | `/search?q=` | 搜歌曲 / 歌单 / 歌手 |
| GET | `/search/suggest?q=` | 输入联想 |
| GET | `/search/hot` | 热搜词 |
| POST | `/search/hot/refresh` | 换一换 |
| GET | `/player` | 播放态 + 队列 |
| POST | `/player/play` | 播放指定歌曲，可同时重置队列 |
| POST | `/player/pause` `/resume` `/toggle` | 暂停 / 继续 / 切换 |
| POST | `/player/next` `/prev` | 上下一首 |
| POST | `/player/seek` | 跳转（`position` 或 `ratio`） |
| PUT | `/player/progress` | 客户端上报进度与播放态 |
| POST | `/player/shuffle` `/repeat` | 随机 / 循环模式 |
| GET | `/player/queue` | 队列 |
| POST | `/player/queue` | 追加（去重） |
| DELETE | `/player/queue/{position}` | 移除一项 |
| DELETE | `/player/queue` | 清空（保留当前曲） |
| GET | `/favorites` | 收藏列表 |
| PUT / DELETE | `/favorites/{id}` | 加入 / 取消收藏 |
| POST | `/favorites/{id}/toggle` | 收藏取反 |
| GET | `/recent` | 最近播放（今天 / 昨天 / 更早 分组） |
| POST | `/recent/{id}` | 记录一次播放 |
| DELETE | `/recent` | 清空 |
| GET / POST | `/downloads` | 下载列表 / 加入下载 |
| DELETE | `/downloads/{id}` `/downloads` | 单条删除 / 清空 |
| GET | `/me/profile` | 资料、统计、菜单（含 `route` 与真实 `count`） |
| GET / PATCH | `/me/settings` | 播放设置 |

## 约定

- 无鉴权，单用户。`player_state` 是单例行（`id=1`）。
- 所有写接口都返回完整播放态，前端一次请求即可同步 UI。
- 错误统一为 `{"error": {"code": "...", "message": "..."}}`，如 `song_not_found`。
- 前端 `public/covers` 与后端 `/covers` 路径一致；接 API 时把图片域名指到 `http://127.0.0.1:8000`，或在 Vite 里加 `/covers` 代理。
