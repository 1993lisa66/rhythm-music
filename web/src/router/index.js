import { createRouter, createWebHashHistory } from 'vue-router'

import Discover from '../views/Discover.vue'
import Library from '../views/Library.vue'
import Search from '../views/Search.vue'
import Profile from '../views/Profile.vue'
import Playlist from '../views/Playlist.vue'
import Album from '../views/Album.vue'
import Albums from '../views/Albums.vue'
import Songs from '../views/Songs.vue'
import Artist from '../views/Artist.vue'
import NowPlaying from '../views/NowPlaying.vue'
import Queue from '../views/Queue.vue'
import Lyrics from '../views/Lyrics.vue'
import Settings from '../views/Settings.vue'
import Recent from '../views/Recent.vue'
import MyLists from '../views/MyLists.vue'
import Favorites from '../views/Favorites.vue'
import Login from '../views/Login.vue'
import { auth, bootstrap } from '../store/auth'
import { ensureAppData } from '../store/data'

const routes = [
  { path: '/', redirect: '/discover' },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { title: '登录', bare: true, public: true }
  },
  {
    path: '/discover',
    name: 'discover',
    component: Discover,
    meta: { tab: 'discover', title: '发现' }
  },
  {
    path: '/library',
    name: 'library',
    component: Library,
    meta: { tab: 'library', title: '乐库' }
  },
  {
    path: '/search',
    name: 'search',
    component: Search,
    meta: { tab: 'search', title: '搜索' }
  },
  {
    path: '/profile',
    name: 'profile',
    component: Profile,
    meta: { tab: 'profile', title: '我的' }
  },
  {
    path: '/playlist/:id',
    name: 'playlist',
    component: Playlist,
    meta: { tab: 'discover', title: '歌单', subpage: true }
  },
  {
    path: '/queue',
    name: 'queue',
    component: Queue,
    meta: { tab: 'discover', title: '播放队列', subpage: true }
  },
  {
    path: '/songs',
    name: 'songs',
    component: Songs,
    meta: { tab: 'library', title: '全部歌曲', subpage: true }
  },
  {
    path: '/albums',
    name: 'albums',
    component: Albums,
    meta: { tab: 'library', title: '全部专辑', subpage: true }
  },
  {
    path: '/album/:name',
    name: 'album',
    component: Album,
    meta: { tab: 'library', title: '专辑', subpage: true }
  },
  {
    path: '/artist/:name',
    name: 'artist',
    component: Artist,
    meta: { tab: 'library', title: '歌手', subpage: true }
  },
  {
    path: '/recent',
    name: 'recent',
    component: Recent,
    meta: { tab: 'profile', title: '最近播放', subpage: true }
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: Favorites,
    meta: { tab: 'profile', title: '我的收藏', subpage: true }
  },
  {
    path: '/mylists',
    name: 'mylists',
    component: MyLists,
    meta: { tab: 'profile', title: '我的歌单', subpage: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: Settings,
    meta: { tab: 'profile', title: '设置', subpage: true }
  },
  {
    path: '/lyrics',
    name: 'lyrics',
    component: Lyrics,
    meta: { tab: '', title: '歌词', immersive: true }
  },
  {
    path: '/now',
    name: 'now',
    component: NowPlaying,
    meta: { tab: '', title: '正在播放', immersive: true }
  },
  { path: '/:pathMatch(.*)*', redirect: '/discover' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  /* 滚动由下方 restoreScroll 自己管：容器是 .page 而不是 window */
  scrollBehavior: () => false
})

/**
 * 滚动位置记忆
 * 应用内真正的滚动容器是 .page（绝对定位 + overflow-y），window 从不滚动，
 * 所以 router 自带的 savedPosition 永远拿不到值。这里按 history entry 记账：
 *   key = 该条历史记录的 position + 当前 hash
 * 离开时存档（beforeEach，此时旧页面还在 DOM 里），返回时回放（afterEach）。
 */
const scrollStore = new Map()
let restoreRun = 0
let lastPosition = null
let pendingPop = false

/* 以路由 fullPath 为键：不依赖 history.state 的写入时机，
   同一路径重复进入时按「最近一次」的位置处理，对返回场景足够准确 */
const routeKey = (route) => (route && route.fullPath) || window.location.hash

const statePosition = () => {
  const state = window.history.state
  return state && typeof state.position === 'number' ? state.position : null
}

/**
 * 判断这次导航是「后退/前进」还是「新开」：
 * push 时 beforeEach 早于 history.push 写入，拿到的还是当前记录；
 * pop 时地址与 state 已经指向目标记录，position 必然和当前记录不同。
 */
router.beforeEach((to, from) => {
  if (!from.name) return
  const page = document.querySelector('.page')
  if (page) scrollStore.set(routeKey(from), Math.round(page.scrollTop))

  const pos = statePosition()
  pendingPop = lastPosition !== null && pos !== null && pos !== lastPosition
})

/**
 * 等新页面挂载后再落位置（切换有 220ms 过渡，元素会被替换），
 * 并且内容高度是数据到位后才撑开的，所以 1.2s 内多补几次把位置坐实。
 */
const settleScroll = (target) => {
  const run = ++restoreRun
  const initial = document.querySelector('.page')

  const apply = () => {
    if (run !== restoreRun) return
    const page = document.querySelector('.page')
    if (!page) return
    const max = page.scrollHeight - page.clientHeight
    if (max <= 0) return
    page.scrollTop = Math.min(target, max)
  }

  let tries = 0
  const waitMount = () => {
    if (run !== restoreRun) return
    const page = document.querySelector('.page')
    if (page && page !== initial) {
      ;[0, 120, 320, 700, 1100].forEach((delay) => window.setTimeout(apply, delay))
      return
    }
    if (tries++ < 45) requestAnimationFrame(waitMount)
    else [0, 200, 600].forEach((delay) => window.setTimeout(apply, delay))
  }
  requestAnimationFrame(waitMount)
}

router.afterEach((to) => {
  const pos = statePosition()
  if (pos !== null) lastPosition = pos

  if (pendingPop) {
    pendingPop = false
    settleScroll(scrollStore.get(routeKey(to)) || 0)
    return
  }
  /* 新开页面一律回顶；同一组件被复用（歌单跳歌单）时也不会残留上一页的位置 */
  settleScroll(0)
})

router.beforeEach(async (to) => {
  await bootstrap()

  if (to.meta.public) {
    return auth.user ? { name: 'discover' } : true
  }

  if (!auth.user) {
    return { name: 'login', query: to.fullPath === '/' ? {} : { redirect: to.fullPath } }
  }

  try {
    await ensureAppData()
  } catch (error) {
    if (error?.status === 401) return { name: 'login' }
  }
  return true
})

export default router
