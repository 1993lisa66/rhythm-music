# 韵律 · 个人音乐 App（Vue 3 实现）

按 Ardot 设计稿（`751605196824333`）1:1 还原的移动端音乐 App 前端，390 × 844 逻辑画布，数据全部来自本地 JSON。

## 技术栈

- Vue 3.4（Composition API + `<script setup>`）
- Vue Router 4（hash 路由）
- Vite 5
- 原生 CSS + CSS 变量（设计令牌），零 UI 框架依赖

## 启动

```bash
npm install
npm run dev      # http://127.0.0.1:5173
npm run build    # 产出 dist/
npm run preview  # 预览构建产物
```

## 目录结构

```
src/
├── components/          公共组件
│   ├── Icon.vue         20+ 手写 SVG 图标（1.8px 描边 / 实心两套）
│   ├── StatusBar.vue    9:41 状态栏（明/暗两态）
│   ├── TabBar.vue       悬浮胶囊导航（5 位，中央 54px 播放键）
│   ├── MiniPlayer.vue   毛玻璃迷你播放条（floating / compact 两态）
│   ├── SongRow.vue      封面列表行（含播放中动效）
│   ├── TrackRow.vue     序号曲目行
│   └── SectionHeader.vue 区块标题 + 右侧入口
├── views/
│   ├── Discover.vue     01 发现
│   ├── Library.vue      02 音乐库（歌曲/歌单/专辑三态）
│   ├── Search.vue       03 搜索（热搜 / 猜你喜欢 / 结果 / 空态）
│   ├── Playlist.vue     04 歌单详情
│   ├── NowPlaying.vue   05 正在播放（深色沉浸）
│   └── Profile.vue      06 我的
├── data/                songs / playlists / discover / library / search / profile / lyrics
├── store/player.js      播放队列、进度、收藏、随机、循环
└── styles/              tokens.css（设计令牌）+ base.css（设备壳与版面）
```

## 坐标约定

页面滚动容器 `top: 44px`（让出状态栏），`.page__canvas` 高 800px，所有绝对定位值 = 设计稿 y − 44。

## 交互

- 底部 5 位胶囊：发现 / 乐库 / 搜索 / 我的 + 中央播放键（进入播放页）
- 迷你播放条：点击展开播放页，右侧按钮播放/暂停
- 播放页：进度条可点击/拖动、键盘 ← → 调进度、空格播放暂停、心形收藏、随机与循环切换
- 搜索：输入即时过滤（歌名/歌手/专辑/流派），热搜 Chip 一键检索，无结果有空状态
- 音乐库：Tab 切换歌曲/歌单/专辑，卡片内容随之替换
- 歌单详情：播放全部 / 随机播放（Fisher-Yates）/ 曲目点击播放

## 注

- 无音频文件，播放进度由 1s ticker 模拟（初始对齐设计稿 `01:28 / 03:42`）。
- 封面为 `public/covers/` 下 24 张真实图片；设计稿中的色块占位已替换为真实封面，标题区保留日落渐变叠层。
