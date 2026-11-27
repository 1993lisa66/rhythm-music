import { createRouter, createWebHashHistory } from 'vue-router'

import Discover from '../views/Discover.vue'
import Library from '../views/Library.vue'
import Search from '../views/Search.vue'
import Profile from '../views/Profile.vue'
import Playlist from '../views/Playlist.vue'
import Album from '../views/Album.vue'
import Albums from '../views/Albums.vue'
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
  scrollBehavior: () => ({ top: 0 })
})

/**
 * 路由守卫：未登录一律去登录页（带 redirect），已登录则先确保基础数据就绪。
 * 登录页自身不加载业务数据，避免刚注册的空账号闪一下别人的内容。
 */
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
