<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import { data, refreshDiscover } from '@/store/data'
import { current, playSong, state } from '@/store/player'
import { coverStyle } from '@/utils/format'
import { toast } from '@/store/toast'

const router = useRouter()

const EMPTY = {
  greeting: '',
  headline: '',
  searchPlaceholder: '搜索歌曲、歌手、歌单',
  featured: { sectionTitle: '今日推荐', more: '', playlist: null },
  moods: { title: '随心听', items: [] },
  recent: { title: '最近播放', more: '', items: [] }
}

const discover = computed(() => data.discover || EMPTY)
const featured = computed(() => discover.value.featured.playlist)
const recent = computed(() => discover.value.recent.items)
const recentIds = computed(() => recent.value.map((s) => s.id))

const TONE = { sage: 'var(--sage)', honey: 'var(--honey)', plum: 'var(--plum)' }

const isRowActive = (song) => current.value.id === song.id && state.playing

const openFeatured = () => {
  if (featured.value) router.push(`/playlist/${featured.value.id}`)
}
const openSearch = () => router.push('/search')

/* 随心听支持两种切片：按流派（genre）或按合集（album） */
const moodSongs = (mood) =>
  mood.album
    ? data.songs.filter((s) => s.album === mood.album)
    : data.songs.filter((s) => s.genre === mood.genre)

const playMood = (mood) => {
  const list = moodSongs(mood)
  if (list.length) playSong(list[0].id, list.map((s) => s.id))
  else router.push({ path: '/search', query: { q: mood.genre } })
}

const playRecent = (song) => playSong(song.id, recentIds.value)
/* 胶囊上标出这个切片有多少首，点之前就知道会播到什么 */
const moodCount = (mood) => moodSongs(mood).length

/* 画布原本固定 800px，绝对定位的行列表再长也撑不开滚动区；按行数撑高
   卡片上下各 7px 内边距 + 每行 60px（与音乐库列表一致），底部留白由 .page::after 统一给 */
const canvasHeight = computed(() => Math.max(800, 576 + 14 + recent.value.length * 60))

onMounted(async () => {
  try {
    await refreshDiscover()
  } catch (error) {
    toast(error?.message || '加载失败')
  }
})
</script>

<template>
  <div class="page">
    <div class="page__canvas" :style="{ height: `${canvasHeight}px` }">
      <p class="greeting">{{ discover.greeting }}</p>
      <h1 class="headline">{{ discover.headline }}</h1>

      <button type="button" class="search" @click="openSearch">
        <Icon name="search" :size="16" :stroke="1.9" />
        <span class="search__ph">{{ discover.searchPlaceholder }}</span>
      </button>

      <SectionHeader class="sec sec--featured" :title="discover.featured.sectionTitle" />

      <button
        v-if="featured"
        type="button"
        class="featured"
        :style="coverStyle(featured.cover, 0.56)"
        @click="openFeatured"
      >
        <span class="featured__badge">{{ featured.featuredBadge }}</span>
        <span class="featured__title">{{ featured.title }}</span>
        <span class="featured__info">{{ featured.info }}</span>
      </button>

      <SectionHeader class="sec sec--moods" :title="discover.moods.title" />

      <div class="moods">
        <button
          v-for="m in discover.moods.items"
          :key="m.name"
          type="button"
          class="mood"
          :style="{ background: TONE[m.tone] }"
          @click="playMood(m)"
        >
          <span class="mood__name">{{ m.name }}</span>
          <span class="mood__sub num">{{ moodCount(m) }} 首</span>
        </button>
      </div>

      <SectionHeader
        class="sec sec--recent"
        :title="discover.recent.title"
        :more="discover.recent.more"
        @more="router.push('/recent')"
      />

      <ul v-if="recent.length" class="recent">
        <li v-for="(song, i) in recent" :key="song.id" class="recent__li">
          <button
            type="button"
            class="rrow"
            :class="{ 'rrow--on': isRowActive(song) }"
            @click="playRecent(song)"
          >
            <span class="rrow__rank num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="rrow__cover" :style="coverStyle(song.cover)">
              <span v-if="isRowActive(song)" class="rrow__playing">
                <Icon name="note" :size="11" :stroke="2" />
              </span>
            </span>
            <span class="rrow__text">
              <span class="rrow__title">{{ song.title }}</span>
              <span class="rrow__sub">{{ song.artist }} · {{ song.album }}</span>
            </span>
            <span v-if="isRowActive(song)" class="rrow__eq" aria-hidden="true">
              <i></i><i></i><i></i>
            </span>
            <span v-else class="rrow__go"><Icon name="play" :size="12" /></span>
          </button>
        </li>
      </ul>

      <p v-else class="recent-empty">还没有播放记录，随便点一首开始吧</p>
    </div>
  </div>
</template>

<style scoped>
.greeting {
  position: absolute;
  left: 24px;
  top: 30px;
  font-size: 15px;
  line-height: 20px;
  color: var(--ink-sub);
}

.headline {
  position: absolute;
  left: 24px;
  top: 56px;
  font-size: 28px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.4px;
  color: var(--ink);
}

/* 搜索框：左右各留 24，随屏宽自适应 */
.search {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 108px;
  height: 48px;
  border-radius: var(--r-btn);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 18px;
  color: var(--placeholder);
  transition: box-shadow 0.18s ease;
}

.search:hover {
  box-shadow: 0 4px 16px rgba(224, 120, 86, 0.14);
}

.search__ph {
  font-size: 14px;
  line-height: 18px;
}

.sec {
  position: absolute;
  left: 24px;
  right: 24px;
}

.sec--featured {
  top: 188px;
}

.sec--moods {
  top: 420px;
}

.sec--recent {
  top: 540px;
}

/* 精选封面：342 × 176 r20（宽度跟随屏幕） */
.featured {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 224px;
  height: 176px;
  border-radius: var(--r-card);
  overflow: hidden;
  background-color: var(--primary);
  box-shadow: var(--shadow-cover);
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.featured::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(120% 90% at 8% 100%, rgba(43, 31, 26, 0.28), transparent 62%);
  pointer-events: none;
}

.featured:active {
  transform: scale(0.99);
}

.featured__badge {
  position: absolute;
  left: 16px;
  top: 16px;
  z-index: 2;
  height: 24px;
  padding: 0 10px;
  border-radius: var(--r-badge);
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  font-size: 11px;
  line-height: 24px;
  letter-spacing: 0.3px;
  backdrop-filter: blur(4px);
}

.featured__title {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 80px;
  font-size: 24px;
  font-weight: 700;
  line-height: 30px;
  color: #fff;
  letter-spacing: 0.2px;
  text-shadow: 0 1px 8px rgba(43, 31, 26, 0.18);
  z-index: 1;
  /* 标题最长两行，超出省略；避免长标题往下压住「13 首」那行 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.featured__info {
  position: absolute;
  left: 16px;
  right: 16px;
  /* 钉在卡片底部，标题一行/两行都不会重叠 */
  bottom: 12px;
  font-size: 12px;
  line-height: 16px;
  color: rgba(255, 243, 224, 0.92);
  z-index: 1;
}

/* 随心听：等分三列，窄屏不会溢出右边 */
.moods {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 450px;
  display: flex;
  gap: 14px;
}

.mood {
  flex: 1 1 0;
  min-width: 0;
  height: 80px;
  border-radius: var(--r-card);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  box-shadow: 0 4px 14px rgba(43, 31, 26, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.mood__name {
  font-size: 16px;
  line-height: 20px;
}

.mood__sub {
  font-size: 11px;
  font-weight: 500;
  line-height: 14px;
  letter-spacing: 0;
  opacity: 0.82;
}

.mood:hover {
  box-shadow: 0 8px 20px rgba(43, 31, 26, 0.14);
}

.mood:active {
  transform: scale(0.96);
}

/* 最近播放：标题 540–564，卡片列表 576 起，与标题留出 12px 呼吸 */
.recent {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 576px;
  padding: 7px 0;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.rrow {
  width: 100%;
  height: 60px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  border-radius: 14px;
  text-align: left;
  transition: background 0.16s ease;
}

.rrow:hover {
  background: rgba(245, 239, 227, 0.6);
}

.rrow:active {
  background: var(--surface-soft);
}

.rrow__rank {
  width: 20px;
  flex: 0 0 20px;
  font-size: 13px;
  line-height: 16px;
  color: var(--placeholder);
  letter-spacing: -0.2px;
}

.rrow--on .rrow__rank {
  color: var(--primary);
  font-weight: 700;
}

.rrow__cover {
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  flex: 0 0 auto;
  background-color: var(--surface-cover);
  box-shadow: 0 2px 6px rgba(43, 31, 26, 0.08);
}

.rrow__playing {
  position: absolute;
  right: -3px;
  bottom: -3px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 2px 5px rgba(224, 120, 86, 0.4);
}

.rrow__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.rrow__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.rrow__sub {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.rrow--on .rrow__title {
  color: var(--primary);
}

.rrow__go {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  color: var(--placeholder);
  opacity: 0;
  transition: opacity 0.16s ease, color 0.16s ease;
}

.rrow:hover .rrow__go {
  opacity: 1;
  color: var(--primary);
}

.rrow__eq {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  padding-bottom: 3px;
}

.rrow__eq i {
  width: 2px;
  border-radius: 1px;
  background: var(--primary);
  animation: eq 0.9s ease-in-out infinite alternate;
}

.rrow__eq i:nth-child(1) { height: 5px; animation-delay: -0.2s; }
.rrow__eq i:nth-child(2) { height: 11px; animation-delay: -0.5s; }
.rrow__eq i:nth-child(3) { height: 7px; animation-delay: -0.35s; }

@keyframes eq {
  from { height: 3px; }
  to { height: 12px; }
}

.recent-empty {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 584px;
  margin: 0;
  padding: 26px 0;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  text-align: center;
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-sub);
}
</style>
