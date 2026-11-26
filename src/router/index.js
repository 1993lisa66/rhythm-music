import { createRouter, createWebHashHistory } from 'vue-router'

import Discover from '../views/Discover.vue'
import Library from '../views/Library.vue'
import Search from '../views/Search.vue'
import Profile from '../views/Profile.vue'
import Playlist from '../views/Playlist.vue'
import NowPlaying from '../views/NowPlaying.vue'
import Queue from '../views/Queue.vue'
import Lyrics from '../views/Lyrics.vue'
import Settings from '../views/Settings.vue'
import Downloads from '../views/Downloads.vue'
import Recent from '../views/Recent.vue'
import MyLists from '../views/MyLists.vue'

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
    meta: { tab: 'discover', title: '歌单', subpage: true }
  },
  {
    path: '/queue',
    name: 'queue',
    component: Queue,
    meta: { tab: 'discover', title: '播放队列', subpage: true }
  },
  {
    path: '/downloads',
    name: 'downloads',
    component: Downloads,
    meta: { tab: 'profile', title: '离线下载', subpage: true }
  },
  {
    path: '/recent',
    name: 'recent',
    component: Recent,
    meta: { tab: 'profile', title: '最近播放', subpage: true }
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

export default router
