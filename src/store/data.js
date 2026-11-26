/**
 * 服务端数据层。
 *
 * 所有内容都来自后端接口，这里只做三件事：
 * 1. 缓存成响应式对象，页面直接读 `data.xxx`；
 * 2. 提供按 id 取歌 / 取歌词的索引；
 * 3. 提供各页面的局部刷新方法（页面 onMounted 时调用，保证跨用户、跨端数据是新的）。
 */

import { reactive } from 'vue'
import { api } from '@/api/client'
import { applySettings } from './settings'

export const data = reactive({
  songs: [],
  playlists: [],
  discover: null,
  library: null,
  albums: null,
  recent: null,
  favorites: null,
  downloads: null,
  profile: null,
  hot: null,
  recommend: null,
  settings: null,
  ready: false
})

export const songsById = reactive({})
const lyricCache = reactive({})

function indexSongs(songs = []) {
  Object.keys(songsById).forEach((key) => delete songsById[key])
  songs.forEach((song) => {
    songsById[song.id] = song
  })
  data.songs = songs
}

export const getSong = (id) => songsById[id]

/** 删除歌曲后同步本地曲库：移除记录并重建 id → song 索引 */
export function removeSongLocal(songId) {
  if (!songId || !songsById[songId]) return
  indexSongs(data.songs.filter((song) => song.id !== songId))
}

/** 歌词按需加载并缓存，切歌时不必重复请求 */
export async function ensureLyrics(songId) {
  if (!songId) return []
  if (lyricCache[songId]) return lyricCache[songId]
  try {
    const payload = await api.lyrics(songId)
    lyricCache[songId] = payload.lines || []
  } catch {
    lyricCache[songId] = []
  }
  return lyricCache[songId]
}

export const lyricsOf = (songId) => lyricCache[songId] || []

/** 在线查到歌词后直接写入缓存，避免再发一次 GET */
export function setLyrics(songId, lines) {
  if (songId) lyricCache[songId] = lines || []
}

/** 首屏必需数据：曲库 + 我的歌单 + 设置；只加载一次，退出登录后重置 */
export async function ensureAppData() {
  if (data.ready) return
  const [songs, playlists, settings] = await Promise.all([
    api.songs({ limit: 2000 }),
    api.myPlaylists(),
    api.settings()
  ])
  indexSongs(songs.items)
  data.playlists = playlists.items
  data.settings = settings
  applySettings(settings)
  data.ready = true
}

/** 首屏 + 首屏页数据 */
export async function loadAll() {
  await ensureAppData()
  await Promise.all([refreshDiscover(), refreshLibrary()])
}

export function resetData() {
  indexSongs([])
  data.playlists = []
  data.discover = null
  data.library = null
  data.albums = null
  data.recent = null
  data.favorites = null
  data.downloads = null
  data.profile = null
  data.hot = null
  data.recommend = null
  data.settings = null
  data.ready = false
  Object.keys(lyricCache).forEach((key) => delete lyricCache[key])
}

export async function refreshDiscover() {
  data.discover = await api.discover()
  return data.discover
}

export async function refreshLibrary() {
  data.library = await api.library()
  return data.library
}

export async function refreshAlbums() {
  const payload = await api.albums()
  data.albums = payload.items
  return payload.items
}

export async function refreshHot() {
  data.hot = await api.hot()
  return data.hot
}

export async function refreshRecommend() {
  data.recommend = await api.recommend()
  return data.recommend
}

export async function refreshPlaylists() {
  const payload = await api.myPlaylists()
  data.playlists = payload.items
  return payload.items
}

export async function refreshRecent() {
  data.recent = await api.recent()
  return data.recent
}

export async function refreshFavorites() {
  data.favorites = await api.favorites()
  return data.favorites
}

export async function refreshDownloads() {
  data.downloads = await api.downloads()
  return data.downloads
}

export async function refreshProfile() {
  data.profile = await api.profile()
  return data.profile
}

export async function refreshSettings() {
  data.settings = await api.settings()
  return data.settings
}
