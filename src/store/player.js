import { reactive, computed } from 'vue'
import songs from '@/data/songs.json'
import lyricsData from '@/data/lyrics.json'
import { clamp } from '@/utils/format'

const byId = Object.fromEntries(songs.map((s) => [s.id, s]))

export const allSongs = songs
export const getSong = (id) => byId[id]
export const getPlaylistSongs = (ids = []) => ids.map((id) => byId[id]).filter(Boolean)

const DEFAULT_QUEUE = [
  'wanfeng',
  'xiaoban',
  'riluo',
  'qinglang',
  'huanghun',
  'xinghe',
  'shanye',
  'chengshiye',
  'manxialai',
  'zaochun',
  'wuye',
  'qingtian'
]

export const state = reactive({
  queue: DEFAULT_QUEUE.slice(),
  index: 0,
  playing: false,
  /** 与设计稿对齐：晚风 01:28 / 03:42 */
  position: 88,
  shuffle: false,
  /** all | one | off */
  repeat: 'all',
  liked: Object.fromEntries(songs.map((s) => [s.id, !!s.liked]))
})

export const current = computed(() => byId[state.queue[state.index]] || songs[0])
export const queueSongs = computed(() => state.queue.map((id) => byId[id]).filter(Boolean))
export const progress = computed(() => clamp(state.position / current.value.duration, 0, 1))
export const elapsedText = computed(() => {
  const m = Math.floor(state.position / 60)
  const s = state.position % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

export const currentLyrics = computed(() => lyricsData[current.value.id]?.lines || [])
export const lyricIndex = computed(() => {
  const lines = currentLyrics.value
  let idx = 0
  lines.forEach((line, i) => {
    if (state.position >= line.t) idx = i
  })
  return idx
})

export const isLiked = (id) => !!state.liked[id]

export function playSong(id, queue) {
  const q = queue && queue.length ? queue.slice() : state.queue.slice()
  let i = q.indexOf(id)
  if (i < 0) {
    q.push(id)
    i = q.length - 1
  }
  state.queue = q
  state.index = i
  state.position = 0
  state.playing = true
}

export function toggle() {
  state.playing = !state.playing
}

/** 队列页：跳到指定位置播放 */
export function playAt(index) {
  if (index < 0 || index >= state.queue.length) return
  state.index = index
  state.position = 0
  state.playing = true
}

/** 追加到队列尾部（自动去重），返回实际新增数量 */
export function enqueue(ids = []) {
  let added = 0
  ids.forEach((id) => {
    if (byId[id] && !state.queue.includes(id)) {
      state.queue.push(id)
      added += 1
    }
  })
  return added
}

/** 从队列移除一项，保持当前播放项索引正确 */
export function removeAt(index) {
  if (state.queue.length <= 1 || index < 0 || index >= state.queue.length) return false
  const wasCurrent = index === state.index
  state.queue.splice(index, 1)
  if (index < state.index) state.index -= 1
  else if (wasCurrent) {
    state.index = Math.min(state.index, state.queue.length - 1)
    state.position = 0
  }
  return true
}

/** 清空队列，仅保留当前播放曲目 */
export function clearQueue() {
  state.queue = [state.queue[state.index]]
  state.index = 0
  state.position = 0
}

export function next(auto = false) {
  if (state.repeat === 'one' && auto) {
    state.position = 0
    return
  }
  if (state.shuffle && state.queue.length > 1) {
    let n = state.index
    while (n === state.index) n = Math.floor(Math.random() * state.queue.length)
    state.index = n
  } else if (state.index >= state.queue.length - 1) {
    if (auto && state.repeat === 'off') {
      state.position = current.value.duration
      state.playing = false
      return
    }
    state.index = 0
  } else {
    state.index += 1
  }
  state.position = 0
  state.playing = true
}

export function prev() {
  if (state.position > 3) {
    state.position = 0
    return
  }
  state.index = state.index <= 0 ? state.queue.length - 1 : state.index - 1
  state.position = 0
  state.playing = true
}

export function seek(ratio) {
  state.position = Math.round(clamp(ratio, 0, 1) * current.value.duration)
}

export function tick() {
  if (!state.playing) return
  const dur = current.value.duration
  if (state.position + 1 >= dur) {
    if (state.repeat === 'one') state.position = 0
    else next(true)
    return
  }
  state.position += 1
}

export function toggleLike(id = current.value.id) {
  state.liked[id] = !state.liked[id]
}

export function toggleShuffle() {
  state.shuffle = !state.shuffle
}

export function cycleRepeat() {
  state.repeat = state.repeat === 'all' ? 'one' : state.repeat === 'one' ? 'off' : 'all'
  return state.repeat
}

/** 按关键字过滤全部曲目（歌名 / 歌手 / 专辑） */
export function searchSongs(keyword) {
  const k = keyword.trim().toLowerCase()
  if (!k) return []
  return songs.filter((s) =>
    [s.title, s.artist, s.album, s.genre].some((t) => t.toLowerCase().includes(k))
  )
}
