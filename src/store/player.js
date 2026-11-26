/**
 * 播放器状态：以服务端为准。
 *
 * 约定：
 * - 所有控制动作都调后端接口，接口直接返回完整播放态，前端整体覆盖即可；
 * - 只有进度条推进是本地做的（每秒 +1s），避免每秒写库；
 *   拖动进度、暂停、切歌时才把进度上报。
 */

import { computed, reactive, watch } from 'vue'
import { api } from '@/api/client'
import { clamp } from '@/utils/format'
import { toast } from './toast'
import { ensureLyrics, lyricsOf, songsById } from './data'

const EMPTY = {
  id: '',
  title: '',
  artist: '',
  album: '',
  cover: '',
  duration: 1,
  liked: false
}

export const state = reactive({
  queue: [],
  current: null,
  index: 0,
  playing: false,
  position: 0,
  duration: 0,
  shuffle: false,
  repeat: 'all',
  liked: {}
})

export const current = computed(() => state.current || EMPTY)
export const queueSongs = computed(() => state.queue)
export const progress = computed(() => clamp(state.position / (state.duration || 1), 0, 1))
export const elapsedText = computed(() => {
  const m = Math.floor(state.position / 60)
  const s = state.position % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})
export const currentLyrics = computed(() => lyricsOf(state.current?.id))
export const lyricIndex = computed(() => {
  const lines = currentLyrics.value
  let index = 0
  lines.forEach((line, i) => {
    if (state.position >= line.t) index = i
  })
  return index
})

export const isLiked = (id) => !!state.liked[id]

/** 用接口返回的播放态整体覆盖本地状态 */
function apply(payload) {
  if (!payload) return
  state.queue = payload.queue || []
  state.current = payload.current || null
  state.index = payload.index || 0
  state.playing = !!payload.playing
  state.position = payload.position || 0
  state.duration = payload.duration || 0
  state.shuffle = !!payload.shuffle
  state.repeat = payload.repeat || 'all'
  state.queue.forEach((song) => {
    state.liked[song.id] = song.liked
  })
  if (payload.current) state.liked[payload.current.id] = payload.liked
  if (payload.current?.id) ensureLyrics(payload.current.id)
}

/** 收藏状态变了以后，同步本地 @id → liked 映射（供列表页复用） */
export function syncLiked(songId, liked) {
  state.liked[songId] = liked
  if (songsById[songId]) songsById[songId].liked = liked
}

async function attempt(run, fallback) {
  try {
    return await run()
  } catch (error) {
    toast(error?.message || fallback)
    return null
  }
}

export async function syncPlayer() {
  const payload = await attempt(() => api.player(), '获取播放状态失败')
  apply(payload)
  return payload
}

export async function playSong(id, queue) {
  if (!id) return
  const payload = await attempt(
    () => api.play({ songId: id, queueIds: queue && queue.length ? queue : null }),
    '播放失败'
  )
  apply(payload)
}

export async function toggle() {
  const payload = await attempt(() => api.toggle(), '操作失败')
  apply(payload)
}

export async function next(auto = false) {
  const payload = await attempt(() => api.next(auto), '切歌失败')
  apply(payload)
}

export async function prev() {
  const payload = await attempt(() => api.prev(), '切歌失败')
  apply(payload)
}

/** 队列页：跳到指定位置播放 */
export async function playAt(index) {
  const song = state.queue[index]
  if (!song) return
  await playSong(song.id)
}

/** 追加到队列（后端自动去重），返回实际新增数量 */
export async function enqueue(ids = []) {
  const before = state.queue.length
  const payload = await attempt(() => api.enqueue(ids), '加入队列失败')
  if (payload) await syncPlayer()
  return Math.max(state.queue.length - before, 0)
}

/** 从队列移除一项；返回是否成功（队列至少保留一首） */
export async function removeAt(index) {
  if (state.queue.length <= 1) return false
  const payload = await attempt(() => api.removeFromQueue(index), '移除失败')
  if (!payload) return false
  apply(payload)
  return true
}

export async function clearQueue() {
  const payload = await attempt(() => api.clearQueue(), '清空队列失败')
  apply(payload)
}

let seekTimer = null
/** 拖动进度：先本地跟手，再防抖上报服务端 */
export function seek(ratio) {
  if (!state.duration) return
  state.position = Math.round(clamp(ratio, 0, 1) * state.duration)
  if (seekTimer) window.clearTimeout(seekTimer)
  seekTimer = window.setTimeout(() => {
    seekTimer = null
    api.progress({ position: state.position }).catch(() => {})
  }, 220)
}

let advancing = false
export function tick() {
  if (!state.playing || !state.duration) return
  if (state.position + 1 >= state.duration) {
    if (state.repeat === 'one') {
      state.position = 0
      return
    }
    if (advancing) return
    advancing = true
    next(true).finally(() => {
      advancing = false
    })
    return
  }
  state.position += 1
}

export async function toggleLike(id = current.value.id) {
  if (!id) return
  const wasLiked = !!state.liked[id]
  syncLiked(id, !wasLiked)
  const payload = await attempt(() => api.toggleFavorite(id), '收藏失败')
  if (!payload) {
    syncLiked(id, wasLiked)
    return
  }
  syncLiked(id, payload.liked)
}

export async function toggleShuffle() {
  const payload = await attempt(() => api.shuffle(), '操作失败')
  apply(payload)
}

export async function cycleRepeat() {
  const payload = await attempt(() => api.repeat(), '操作失败')
  apply(payload)
  return state.repeat
}

/** 关键字搜索：直接在已加载的曲库里过滤，保证输入即出结果 */
export function searchSongs(keyword) {
  const k = keyword.trim().toLowerCase()
  if (!k) return []
  return Object.values(songsById).filter((song) =>
    [song.title, song.artist, song.album, song.genre].some((text) =>
      String(text || '').toLowerCase().includes(k)
    )
  )
}

/** 首次拿到播放态后预加载当前曲歌词 */
watch(
  () => state.current?.id,
  (id) => {
    if (id) ensureLyrics(id)
  }
)
