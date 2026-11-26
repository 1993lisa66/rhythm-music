/**
 * 真实音频播放：单个 <audio> 元素与播放态双向同步。
 *
 * 只有曲目带 audio（后端签发的私有 Bucket 地址）时才启用：
 * - 切歌 → 换 src，按 playing 决定播/停；
 * - 音频的 timeupdate 反过来驱动进度，播放期间关掉模拟走秒（setExternalClock）；
 * - 拖动进度条时按漂移纠偏 currentTime，避免回弹；
 * - 播完按 repeat=one 重播，其余交给 next(true) 切歌；
 * - 浏览器拦下自动播放时退回模拟走秒（进度照走，只是没声音）。
 *
 * 没有 audio 的曲目不受影响，仍走 player.js 里原有的模拟播放。
 */

import { watch } from 'vue'
import { api } from '@/api/client'
import { current, next, setExternalClock, state } from './player'

let element = null
let loadedUrl = ''

function ensure() {
  if (element || typeof window === 'undefined') return element

  element = new Audio()
  element.preload = 'auto'

  element.addEventListener('loadedmetadata', () => {
    if (Number.isFinite(element.duration) && element.duration > 1) {
      state.duration = Math.round(element.duration)
    }
    /* 恢复上次听到的位置（服务端播放态里的 position） */
    const resume = Math.min(state.position || 0, Math.max(element.duration - 1, 0))
    if (resume > 0.5 && Math.abs(element.currentTime - resume) > 1.5) element.currentTime = resume
    if (state.playing) autoPlay()
  })

  element.addEventListener('timeupdate', () => {
    if (!state.playing) return
    const seconds = Math.floor(element.currentTime)
    if (seconds !== state.position) state.position = seconds
  })

  element.addEventListener('play', () => setExternalClock(true))
  element.addEventListener('pause', () => setExternalClock(false))

  element.addEventListener('ended', () => {
    setExternalClock(false)
    if (state.repeat === 'one') {
      element.currentTime = 0
      state.position = 0
      autoPlay()
      return
    }
    next(true)
  })

  return element
}

/** 播放失败（多为自动播放策略）不当错误抛给用户，退回模拟走秒即可 */
function autoPlay() {
  if (!element || !loadedUrl) return
  /* 暂停时拖过进度条的话，这里把播放位置补齐再起播 */
  const target = state.position || 0
  if (!element.seeking && Math.abs(element.currentTime - target) > 1.5) {
    element.currentTime = target
  }
  element.play().catch(() => setExternalClock(false))
}

function release() {
  loadedUrl = ''
  setExternalClock(false)
  if (!element) return
  element.pause()
  element.removeAttribute('src')
  element.load()
}

function attach(url) {
  const audio = ensure()
  if (!audio) return
  const target = url || ''
  if (!target) {
    if (loadedUrl) release()
    return
  }
  if (target === loadedUrl) return
  loadedUrl = target
  audio.src = target
  audio.load()
}

/* ------------------------------------------------------------------ 换签
 * 私有 Bucket 的地址带 Expires，页面开太久会过期（403）。
 * 这里每分钟看一眼当前曲目的地址，剩余不足 10 分钟就调 /assets/sign 换新的；
 * 换完只是把 state 里的地址替换掉，播放位置由 attach/loadedmetadata 续上。
 */
const RENEW_AHEAD = 600
const RENEW_INTERVAL = 60 * 1000

function expiresAt(url) {
  const matched = /[?&]Expires=(\d+)/.exec(url || '')
  return matched ? Number(matched[1]) : 0
}

/** 从签名地址里还原对象键；本地回落路径（/covers/x.jpg）也适用 */
function objectKey(url) {
  if (!url) return ''
  try {
    return new URL(url, window.location.origin).pathname.replace(/^\/+/, '')
  } catch {
    return String(url).split('?')[0].replace(/^\/+/, '')
  }
}

let renewing = false

async function renewAssets() {
  const song = current.value
  if (renewing || !song?.id) return
  const keys = [...new Set([objectKey(song.audio), objectKey(song.cover)].filter(Boolean))]
  if (!keys.length) return

  renewing = true
  try {
    const payload = await api.signAssets(keys)
    const fresh = new Map((payload?.items || []).map((item) => [item.key, item.url]))
    if (!fresh.size) return
    const patch = (target) => {
      if (!target) return
      const audio = fresh.get(objectKey(target.audio))
      if (audio) target.audio = audio
      const cover = fresh.get(objectKey(target.cover))
      if (cover) target.cover = cover
    }
    patch(state.current)
    /* 队列里同一首也换掉，队列页/迷你播放条才不会突然白图 */
    state.queue.forEach((item) => {
      if (item.id === song.id) patch(item)
    })
  } catch {
    /* 换签失败不打断播放，下一分钟再试 */
  } finally {
    renewing = false
  }
}

function checkExpiry() {
  const url = current.value.audio || current.value.cover
  const expires = expiresAt(url)
  /* 没有 Expires 说明是本地回落路径，不需要换签 */
  if (!expires) return
  if (expires - Math.floor(Date.now() / 1000) < RENEW_AHEAD) renewAssets()
}

export function initAudio() {
  const audio = ensure()
  if (!audio) return

  /* 切歌：换源；新曲若该继续播就播。地址一变就顺手检查是否快过期 */
  watch(
    () => current.value.audio,
    (url) => {
      attach(url)
      if (url && state.playing) autoPlay()
      checkExpiry()
    },
    { immediate: true }
  )

  /* 播放 / 暂停 */
  watch(
    () => state.playing,
    (playing) => {
      if (!loadedUrl) return
      if (playing) autoPlay()
      else audio.pause()
    }
  )

  /* 拖进度：只在明显漂移时纠偏，避免和 timeupdate 打架 */
  watch(
    () => state.position,
    (seconds) => {
      if (!loadedUrl || audio.seeking || audio.paused) return
      if (Math.abs(audio.currentTime - seconds) > 1.5) audio.currentTime = seconds
    }
  )

  /* 之后每分钟巡检一次：地址是否快到期 */
  window.setInterval(checkExpiry, RENEW_INTERVAL)
}
