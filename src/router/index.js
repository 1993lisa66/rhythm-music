import { createRouter, createWebHashHistory } from 'vue-router'

import Discover from '../views/Discover.vue'
import Library from '../views/Library.vue'
import Search from '../views/Search.vue'
import Profile from '../views/Profile.vue'
import Playlist from '../views/Playlist.vue'
import NowPlaying from '../views/NowPlaying.vue'

const routes = [
  { path: '/', redirect: '/discover' },
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
    meta: { tab: 'discover', title: '歌单' }
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

export default router
