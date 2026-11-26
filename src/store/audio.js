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

export function initAudio() {
  const audio = ensure()
  if (!audio) return

  /* 切歌：换源；新曲若该继续播就播 */
  watch(
    () => current.value.audio,
    (url) => {
      attach(url)
      if (url && state.playing) autoPlay()
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
}
