<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import PickPlaylistSheet from '@/components/PickPlaylistSheet.vue'
import { api } from '@/api/client'
import { removeSongLocal } from '@/store/data'
import { settings } from '@/store/settings'
import { toast } from '@/store/toast'
import { goBack } from '@/utils/nav'
import {
  current,
  currentLyrics,
  elapsedText,
  lyricIndex,
  next,
  prev,
  progress,
  seek,
  state,
  syncPlayer,
  toggle,
  toggleLike,
  toggleShuffle,
  cycleRepeat
} from '@/store/player'
import { coverStyle, fmtTime } from '@/utils/format'

const router = useRouter()
const barRef = ref(null)
const dragging = ref(false)
const sheet = ref(false)
const pickPlaylist = ref(false)
/* 删除是破坏性操作：在同一个面板里切到二次确认态，避免误触 */
const confirming = ref(false)
const removing = ref(false)

const back = () => goBack(router, '/discover')

const actions = computed(() => [
  { key: 'like', label: liked.value ? '取消收藏' : '收藏歌曲', icon: 'heart', active: liked.value },
  { key: 'add-to-playlist', label: '添加到歌单', icon: 'plus' },
  { key: 'lyrics', label: '查看歌词', icon: 'quote' },
  { key: 'queue', label: '播放队列', icon: 'queue' },
  { key: 'artist', label: '查看歌手', icon: 'mic' },
  { key: 'album', label: '查看专辑', icon: 'note' },
  { key: 'share', label: '分享歌曲', icon: 'share' },
  { key: 'remove', label: '删除歌曲资源', icon: 'trash', danger: true }
])

const sheetTitle = computed(() => (confirming.value ? '删除歌曲资源？' : current.value.title))
const sheetSubtitle = computed(() =>
  confirming.value
    ? `将从曲库移除《${current.value.title}》，并删除音频与封面文件，无法恢复`
    : `${current.value.artist} · ${current.value.album}`
)
const sheetActions = computed(() =>
  confirming.value ? [{ key: 'confirm', label: '确认删除', icon: 'trash', danger: true }] : actions.value
)
const sheetCancel = computed(() => (confirming.value ? '保留歌曲' : '取消'))

const closeSheet = () => {
  sheet.value = false
  confirming.value = false
}

const openSheet = () => {
  confirming.value = false
  sheet.value = true
}

const openQueue = () => router.push('/queue')
const openLyrics = () => router.push('/lyrics')

/** 删除当前歌曲：后端清曲库记录 + OSS 资源，前端同步本地曲库并刷新播放态 */
const removeSong = async () => {
  if (removing.value) return
  const song = current.value
  if (!song.id) return
  removing.value = true
  try {
    await api.deleteSong(song.id)
    removeSongLocal(song.id)
    closeSheet()
    toast('已删除歌曲资源')
    await syncPlayer()
    if (!current.value.id) back()
  } catch (error) {
    toast(error?.message || '删除失败')
  } finally {
    removing.value = false
  }
}

const onPick = async (key) => {
  if (key === 'remove') {
    confirming.value = true
    return
  }
  if (key === 'confirm') {
    await removeSong()
    return
  }
  sheet.value = false
  if (key === 'like') {
    toggleLike()
    toast(liked.value ? '已收藏' : '已取消收藏')
  } else if (key === 'add-to-playlist') {
    pickPlaylist.value = true
  } else if (key === 'queue') {
    openQueue()
  } else if (key === 'artist') {
    // 曲目里的歌手是多歌手拼接（如「甲、乙」），单看某一位会漏歌，按原样查整串
    if (current.value.artist) {
      router.push(`/artist/${encodeURIComponent(current.value.artist)}`)
    }
  } else if (key === 'lyrics') {
    openLyrics()
  } else if (key === 'album') {
    if (current.value.album) router.push(`/album/${encodeURIComponent(current.value.album)}`)
    else router.push({ path: '/search', query: { q: current.value.title } })
  } else if (key === 'share') {
    try {
      await navigator.clipboard.writeText(window.location.href)
      toast('歌曲链接已复制')
    } catch {
      toast('当前环境不支持复制链接')
    }
  }
}

const totalText = computed(() => fmtTime(current.value.duration))
const liked = computed(() => !!state.liked[current.value.id])
const prevLine = computed(() => currentLyrics.value[lyricIndex.value - 1]?.text || '')
const curLine = computed(() => currentLyrics.value[lyricIndex.value]?.text || '暂无歌词')

const repeatLabel = computed(() =>
  state.repeat === 'one' ? '单曲循环' : state.repeat === 'off' ? '顺序播放' : '列表循环'
)

const seekTo = (clientX) => {
  const el = barRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  seek((clientX - rect.left) / rect.width)
}

const onDown = (e) => {
  dragging.value = true
  seekTo(e.clientX)
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

const onMove = (e) => {
  if (dragging.value) seekTo(e.clientX)
}

const onUp = () => {
  dragging.value = false
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
}

onUnmounted(onUp)

const onKey = (e) => {
  if (e.key === 'ArrowRight') {
    e.preventDefault()
    seek(progress.value + 0.02)
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    seek(progress.value - 0.02)
  } else if (e.key === ' ' || e.key === 'Enter') {
    e.preventDefault()
    toggle()
  }
}
</script>

<template>
  <div class="page page--dark">
    <div class="page__canvas">
      <button type="button" class="nav nav--back" aria-label="返回" @click="back">
        <Icon name="back" :size="22" :stroke="2" />
      </button>
      <p class="nav__title">正在播放</p>
      <button
        type="button"
        class="nav nav--more"
        aria-label="更多操作"
        aria-haspopup="dialog"
        @click="openSheet"
      >
        <Icon name="more" :size="22" />
      </button>

      <span class="glow" aria-hidden="true"></span>
      <!-- 点封面直接进歌词页，符合「看图看词」的手势直觉 -->
      <button
        type="button"
        class="cover"
        :style="coverStyle(current.cover)"
        aria-label="查看歌词"
        @click="openLyrics"
      ></button>

      <h1 class="song">{{ current.title }}</h1>
      <p class="artist">{{ current.artist }} · {{ current.album }}</p>

      <button
        type="button"
        class="like"
        :class="{ 'like--on': liked }"
        :aria-pressed="liked"
        :aria-label="liked ? '取消收藏' : '收藏'"
        @click="toggleLike()"
      >
        <Icon name="heart" :size="26" :stroke="1.7" :filled="liked" />
      </button>

      <div
        ref="barRef"
        class="bar"
        role="slider"
        tabindex="0"
        aria-label="播放进度"
        :aria-valuemin="0"
        :aria-valuemax="100"
        :aria-valuenow="Math.round(progress * 100)"
        :aria-valuetext="`${elapsedText} / ${totalText}`"
        @pointerdown.prevent="onDown"
        @keydown="onKey"
      >
        <span class="bar__track"></span>
        <span class="bar__fill" :style="{ width: `${progress * 100}%` }"></span>
        <span class="bar__dot" :style="{ left: `calc(${progress * 100}% - 7px)` }"></span>
      </div>

      <span class="time time--now num">{{ elapsedText }}</span>
      <span class="time time--total num">{{ totalText }}</span>

      <div class="controls">
        <button
          type="button"
          class="ctrl ctrl--shuffle"
          :class="{ 'ctrl--on': state.shuffle }"
          :aria-pressed="state.shuffle"
          aria-label="随机播放"
          @click="toggleShuffle"
        >
          <Icon name="shuffle" :size="22" :stroke="1.7" />
        </button>

        <button type="button" class="ctrl ctrl--prev" aria-label="上一首" @click="prev">
          <Icon name="prev" :size="24" />
        </button>

        <button
          type="button"
          class="ctrl ctrl--play"
          :aria-label="state.playing ? '暂停' : '播放'"
          @click="toggle"
        >
          <Icon :name="state.playing ? 'pause' : 'play'" :size="26" />
        </button>

        <button type="button" class="ctrl ctrl--next" aria-label="下一首" @click="next(false)">
          <Icon name="next" :size="24" />
        </button>

        <button
          type="button"
          class="ctrl ctrl--repeat"
          :class="{ 'ctrl--on': state.repeat !== 'off' }"
          :aria-label="repeatLabel"
          :title="repeatLabel"
          @click="cycleRepeat"
        >
          <Icon name="repeat" :size="22" :stroke="1.7" />
          <span v-if="state.repeat === 'one'" class="ctrl__badge">1</span>
        </button>
      </div>

      <div v-if="settings.showLyrics" class="lyrics">
        <div class="lyrics__head">
          <span class="lyrics__label">
            <Icon name="quote" :size="16" :stroke="1.8" />
            歌词
          </span>
          <button type="button" class="lyrics__more" @click="openLyrics">展开 ›</button>
        </div>
        <p class="lyrics__line lyrics__line--prev">{{ prevLine }}</p>
        <p class="lyrics__line lyrics__line--cur">{{ curLine }}</p>
      </div>

      <div class="tools">
        <button type="button" class="tool" aria-label="播放队列" @click="openQueue">
          <Icon name="queue" :size="20" :stroke="1.8" />
          <span>队列</span>
        </button>
        <button
          type="button"
          class="tool tool--on"
          :aria-pressed="liked"
          aria-label="收藏"
          @click="toggleLike()"
        >
          <Icon name="heart" :size="20" :stroke="1.8" :filled="liked" />
          <span>收藏</span>
        </button>
        <button type="button" class="tool" aria-label="更多" @click="openSheet">
          <Icon name="more" :size="20" />
          <span>更多</span>
        </button>
      </div>
    </div>

    <ActionSheet
      :open="sheet"
      :title="sheetTitle"
      :subtitle="sheetSubtitle"
      :actions="sheetActions"
      :cancel-text="sheetCancel"
      @pick="onPick"
      @close="closeSheet"
    />

    <PickPlaylistSheet
      :open="pickPlaylist"
      :song-id="current.id"
      :song-title="current.title"
      @close="pickPlaylist = false"
    />
  </div>
</template>

<style scoped>
.nav {
  position: absolute;
  top: 36px;
  width: 22px;
  height: 22px;
  color: var(--on-dark);
  display: grid;
  place-items: center;
  opacity: 0.86;
  /* 抬头于居中标题之上，避免按钮被全宽文本层遮挡而点不到 */
  z-index: 2;
}

/* 视觉仍是 22px，实际点击热区外扩到 42px */
.nav::after {
  content: '';
  position: absolute;
  inset: -10px;
}

.nav--back {
  left: 24px;
}

.nav--more {
  right: 24px;
}

.nav__title {
  position: absolute;
  top: 37px;
  /* 左右各留 56px，从几何上就不与两枚 22px 按钮重叠 */
  left: 56px;
  right: 56px;
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  line-height: 20px;
  color: var(--on-dark);
  letter-spacing: 0.4px;
  /* 纯装饰层：不吃指针事件，否则会挡住左右两个按钮 */
  pointer-events: none;
  z-index: 1;
}

/* 封面背后的暖色光晕：居中，不随屏宽拉伸 */
.glow {
  position: absolute;
  left: 50%;
  margin-left: -171px;
  top: 60px;
  width: 342px;
  height: 342px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 126, 84, 0.34) 0%, rgba(255, 77, 141, 0.12) 45%, transparent 68%);
  filter: blur(18px);
  pointer-events: none;
}

.cover {
  position: absolute;
  left: 50%;
  margin-left: -147px;
  top: 90px;
  width: 294px;
  height: 294px;
  padding: 0;
  border: 0;
  display: block;
  border-radius: 28px;
  background-color: #3a2b23;
  box-shadow: 0 16px 40px rgba(255, 125, 85, 0.3);
  overflow: hidden;
}

.cover__note {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 66px;
  height: 66px;
  border-radius: 50%;
  background: rgba(43, 31, 26, 0.3);
  color: rgba(255, 243, 224, 0.92);
  display: grid;
  place-items: center;
  backdrop-filter: blur(6px);
}

.song {
  position: absolute;
  left: 24px;
  right: 80px;
  top: 418px;
  font-size: 28px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.4px;
  color: var(--on-dark);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.artist {
  position: absolute;
  left: 24px;
  right: 80px;
  top: 458px;
  font-size: 14px;
  line-height: 20px;
  color: var(--on-dark-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.like {
  position: absolute;
  right: 20px;
  top: 422px;
  width: 26px;
  height: 26px;
  color: rgba(255, 243, 224, 0.72);
  display: grid;
  place-items: center;
  transition: color 0.18s ease, transform 0.18s ease;
}

.like--on {
  color: #ff7d85;
}

.like:active {
  transform: scale(0.88);
}

/* 进度条：4px 轨道 + 14px 圆点，热区抬到 20px */
.bar {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 496px;
  height: 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  touch-action: none;
}

.bar__track {
  position: absolute;
  left: 0;
  right: 0;
  top: 8px;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.19);
}

.bar__fill {
  position: absolute;
  left: 0;
  top: 8px;
  height: 4px;
  border-radius: 2px;
  background: var(--primary);
  transition: width 0.25s linear;
}

.bar__dot {
  position: absolute;
  top: 3px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--on-dark);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  transition: left 0.25s linear;
}

.time {
  position: absolute;
  top: 518px;
  font-size: 12px;
  color: var(--on-dark-sub);
}

.time--now {
  left: 24px;
}

.time--total {
  right: 24px;
}

/* 控制区 */
.controls {
  position: absolute;
  left: 0;
  right: 0;
  top: 544px;
  height: 80px;
}

.ctrl {
  position: absolute;
  color: var(--on-dark);
  display: grid;
  place-items: center;
  transition: color 0.18s ease, transform 0.16s ease;
}

.ctrl:active {
  transform: scale(0.9);
}

.ctrl--shuffle {
  left: 30px;
  top: 22px;
  width: 22px;
  height: 22px;
  color: var(--on-dark-sub);
}

.ctrl--prev {
  left: 94px;
  top: 20px;
  width: 24px;
  height: 24px;
}

.ctrl--next {
  left: 272px;
  top: 20px;
  width: 24px;
  height: 24px;
}

.ctrl--repeat {
  left: 338px;
  top: 22px;
  width: 22px;
  height: 22px;
  color: var(--on-dark-sub);
}

.ctrl--on {
  color: var(--primary);
}

.ctrl--play {
  left: 155px;
  top: 0;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  box-shadow: 0 8px 24px rgba(224, 120, 86, 0.42), 0 0 32px rgba(224, 120, 86, 0.3);
}

.ctrl--play:active {
  transform: scale(0.96);
}

.ctrl__badge {
  position: absolute;
  right: -4px;
  bottom: -2px;
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  font-size: 8px;
  line-height: 11px;
  text-align: center;
  font-family: var(--font-num);
}

/* 歌词预览卡 */
.lyrics {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 654px;
  height: 86px;
  border-radius: var(--r-card);
  background: rgba(255, 255, 255, 0.08);
  padding: 12px 16px;
  overflow: hidden;
}

.lyrics__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 18px;
}

.lyrics__label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  letter-spacing: 0.3px;
}

.lyrics__more {
  font-size: 11px;
  color: var(--on-dark-sub);
}

.lyrics__line {
  text-align: center;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.lyrics__line--prev {
  margin-top: 6px;
  font-size: 13px;
  line-height: 18px;
  color: rgba(212, 165, 116, 0.72);
}

.lyrics__line--cur {
  margin-top: 2px;
  font-size: 14px;
  font-weight: 700;
  line-height: 20px;
  color: var(--on-dark);
}

/* 底部操作 */
.tools {
  position: absolute;
  left: 0;
  right: 0;
  top: 748px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
}

.tool {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  line-height: 12px;
  color: var(--on-dark-sub);
  letter-spacing: 0.3px;
  transition: color 0.16s ease;
}

.tool--on {
  color: var(--primary);
}

/* 控制条改成等分排布：390 宽的坐标在 430/360 屏上会偏，交给 flex 自己算 */
.controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
}

.ctrl {
  position: relative;
  left: auto;
  top: auto;
}
</style>
