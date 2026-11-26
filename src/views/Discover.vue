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

const playMood = (mood) => {
  const list = data.songs.filter((s) => s.genre === mood.genre)
  if (list.length) playSong(list[0].id, list.map((s) => s.id))
  else router.push({ path: '/search', query: { q: mood.genre } })
}

const playRecent = (song) => playSong(song.id, recentIds.value)

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
    <div class="page__canvas">
      <p class="greeting">{{ discover.greeting }}</p>
      <h1 class="headline">{{ discover.headline }}</h1>

      <button type="button" class="search" @click="openSearch">
        <Icon name="search" :size="16" :stroke="1.9" />
        <span class="search__ph">{{ discover.searchPlaceholder }}</span>
      </button>

      <SectionHeader
        class="sec sec--featured"
        :title="discover.featured.sectionTitle"
        :more="discover.featured.more"
        @more="router.push('/library')"
      />

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
          {{ m.name }}
        </button>
      </div>

      <SectionHeader
        class="sec sec--recent"
        :title="discover.recent.title"
        :more="discover.recent.more"
        @more="router.push('/recent')"
      />

      <ul v-if="recent.length" class="recent">
        <li v-for="song in recent" :key="song.id">
          <button
            type="button"
            class="rrow"
            :class="{ 'rrow--on': isRowActive(song) }"
            @click="playRecent(song)"
          >
            <span class="rrow__cover" :style="coverStyle(song.cover)"></span>
            <span class="rrow__text">
              <span class="rrow__title">{{ song.title }}</span>
              <span class="rrow__sub">{{ song.artist }} · {{ song.album }}</span>
            </span>
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

/* 搜索框：342 × 48 r24 */
.search {
  position: absolute;
  left: 24px;
  top: 108px;
  width: 342px;
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

/* 精选封面：342 × 176 r20 */
.featured {
  position: absolute;
  left: 24px;
  top: 224px;
  width: 342px;
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
}

.featured__info {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 116px;
  font-size: 12px;
  line-height: 16px;
  color: rgba(255, 243, 224, 0.92);
  z-index: 1;
}

/* 随心听：3 × 104×80 */
.moods {
  position: absolute;
  left: 24px;
  top: 450px;
  display: flex;
  gap: 14px;
}

.mood {
  width: 104px;
  height: 80px;
  border-radius: var(--r-card);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  display: grid;
  place-items: center;
  box-shadow: 0 4px 14px rgba(43, 31, 26, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.mood:hover {
  box-shadow: 0 8px 20px rgba(43, 31, 26, 0.14);
}

.mood:active {
  transform: scale(0.96);
}

/* 最近播放：标题 540–564，列表 576 起，与标题留出 12px 呼吸 */
.recent {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 576px;
}

.rrow {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  gap: 16px;
  text-align: left;
  border-radius: 12px;
  transition: background 0.16s ease;
}

.rrow:hover {
  background: rgba(255, 255, 255, 0.55);
}

.rrow__cover {
  width: 36px;
  height: 36px;
  border-radius: var(--r-thumb);
  flex: 0 0 auto;
  background-color: var(--surface-cover);
}

.rrow__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.rrow__title {
  font-size: 15px;
  font-weight: 500;
  line-height: 19px;
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
</style>
