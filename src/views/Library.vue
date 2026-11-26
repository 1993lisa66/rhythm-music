<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import SongRow from '@/components/SongRow.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import { data, refreshAlbums, refreshLibrary } from '@/store/data'
import { current, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle, fmtTime } from '@/utils/format'

const router = useRouter()

const EMPTY = {
  title: '音乐库',
  searchPlaceholder: '搜索我的音乐',
  tabs: ['歌曲', '歌单', '专辑'],
  recent: { title: '最近添加', more: '', items: [] },
  playlists: { title: '我的歌单', items: [] }
}

const library = computed(() => data.library || EMPTY)
/* tab 用「选中值」而不是下标，首屏数据回来前留空，由 activeTab 兜底到第一个 */
const tab = ref('')
const activeTab = computed(() => tab.value || library.value.tabs[0] || '歌曲')

const SORTS = [
  { key: 'default', label: '默认顺序' },
  { key: 'title', label: '按歌名排序' },
  { key: 'duration', label: '按时长排序' },
  { key: 'artist', label: '按歌手排序' }
]

const sortKey = ref('default')
const filterOpen = ref(false)

const sortActions = computed(() =>
  SORTS.map((s) => ({ key: s.key, label: s.label, active: sortKey.value === s.key }))
)

const songRows = computed(() => {
  /* 首屏已加载整张曲库，歌曲 tab 展示全部；未加载完才回落到聚合页的示例列表 */
  const rows = (data.songs.length ? data.songs : library.value.recent.items).slice()
  if (sortKey.value === 'default') return rows
  if (sortKey.value === 'title') rows.sort((a, b) => a.title.localeCompare(b.title, 'zh-Hans-CN'))
  else if (sortKey.value === 'duration') rows.sort((a, b) => a.duration - b.duration)
  else if (sortKey.value === 'artist') rows.sort((a, b) => a.artist.localeCompare(b.artist, 'zh-Hans-CN'))
  return rows
})

const songIds = computed(() => songRows.value.map((s) => s.id))
const playlistRows = computed(() => library.value.playlists.items)
/* 专辑视图直接用 /library/albums 的聚合结果，避免前端再猜分组口径 */
const albumRows = computed(() => data.albums || [])

/* 固定 800px 画布会把长列表截断，按实际行数撑开整个滚动区 */
const rowCount = computed(() => {
  if (activeTab.value === '歌曲') return songRows.value.length
  if (activeTab.value === '歌单') return playlistRows.value.length
  return albumRows.value.length
})
const cardHeight = computed(() => Math.max(220, rowCount.value * 60 + 14))
const playlistHeaderTop = computed(() => 242 + cardHeight.value + 14)
const playlistGridTop = computed(() => playlistHeaderTop.value + 36)
const canvasHeight = computed(() =>
  Math.max(800, playlistGridTop.value + Math.ceil(playlistRows.value.length / 2) * 164 + 140)
)

const isRowActive = (song) => current.value.id === song.id && state.playing

const playRow = (song) => playSong(song.id, songIds.value)
const playAlbum = (album) => {
  if (album.trackIds.length) playSong(album.trackIds[0], album.trackIds)
}
const openPlaylist = (p) => router.push(`/playlist/${p.id}`)

const pickSort = (key) => {
  sortKey.value = key
  filterOpen.value = false
  const label = SORTS.find((s) => s.key === key)?.label || ''
  toast(`已切换：${label}`)
}

onMounted(async () => {
  try {
    await Promise.all([refreshLibrary(), refreshAlbums()])
  } catch (error) {
    toast(error?.message || '加载音乐库失败')
  }
})
</script>

<template>
  <div class="page">
    <div class="page__canvas" :style="{ height: `${canvasHeight}px` }">
      <h1 class="title">{{ library.title }}</h1>

      <button
        type="button"
        class="filter"
        :class="{ 'filter--on': sortKey !== 'default' }"
        aria-label="筛选与排序"
        aria-haspopup="dialog"
        @click="filterOpen = true"
      >
        <Icon name="filter" :size="20" :stroke="1.8" />
      </button>

      <div class="tabs" role="tablist" aria-label="音乐库分类">
        <button
          v-for="t in library.tabs"
          :key="t"
          type="button"
          role="tab"
          class="tab"
          :class="{ 'tab--on': activeTab === t }"
          :aria-selected="activeTab === t"
          @click="tab = t"
        >
          {{ t }}
        </button>
      </div>

      <button type="button" class="search" @click="router.push('/search')">
        <Icon name="search" :size="16" :stroke="1.9" />
        <span>{{ library.searchPlaceholder }}</span>
      </button>

      <SectionHeader
        class="sec sec--recent"
        :title="library.recent.title"
        :more="library.recent.more"
        @more="router.push('/recent')"
      />

      <div class="card" :style="{ height: `${cardHeight}px` }">
        <template v-if="activeTab === '歌曲'">
          <SongRow
            v-for="song in songRows"
            :key="song.id"
            :song="song"
            :active="isRowActive(song)"
            @select="playRow"
          />
        </template>

        <template v-else-if="activeTab === '歌单'">
          <button
            v-for="p in playlistRows"
            :key="p.id"
            type="button"
            class="crow"
            @click="openPlaylist(p)"
          >
            <span class="crow__cover" :style="coverStyle(p.cover)"></span>
            <span class="crow__text">
              <span class="crow__title">{{ p.title }}</span>
              <span class="crow__sub">{{ p.count }} 首 · {{ p.durationText }}</span>
            </span>
            <Icon class="crow__go" name="chevron" :size="14" :stroke="1.8" />
          </button>
        </template>

        <template v-else>
          <button
            v-for="a in albumRows"
            :key="a.name"
            type="button"
            class="crow"
            @click="playAlbum(a)"
          >
            <span class="crow__cover" :style="coverStyle(a.cover)"></span>
            <span class="crow__text">
              <span class="crow__title">{{ a.name }}</span>
              <span class="crow__sub">{{ a.artist }}</span>
            </span>
            <span class="crow__dur num">{{ fmtTime(a.duration) }}</span>
          </button>
        </template>
      </div>

      <SectionHeader
        class="sec sec--playlists"
        :style="{ top: `${playlistHeaderTop}px` }"
        :title="library.playlists.title"
        more="全部 ›"
        @more="router.push('/mylists')"
      />

      <div class="pls" :style="{ top: `${playlistGridTop}px` }">
        <button
          v-for="p in playlistRows"
          :key="p.id"
          type="button"
          class="pl"
          @click="openPlaylist(p)"
        >
          <span class="pl__cover" :style="coverStyle(p.cover)">
            <span class="pl__count">{{ p.count }} 首</span>
          </span>
          <span class="pl__title">{{ p.title }}</span>
        </button>
      </div>
    </div>

    <ActionSheet
      :open="filterOpen"
      title="排序方式"
      :actions="sortActions"
      @pick="pickSort"
      @close="filterOpen = false"
    />
  </div>
</template>

<style scoped>
.title {
  position: absolute;
  left: 24px;
  top: 30px;
  font-size: 28px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.4px;
  color: var(--ink);
}

.filter {
  position: absolute;
  right: 22px;
  top: 36px;
  width: 20px;
  height: 20px;
  color: var(--ink);
  display: grid;
  place-items: center;
  transition: color 0.16s ease, transform 0.16s ease;
}

.filter:hover {
  color: var(--primary);
  transform: translateY(-1px);
}

.filter--on {
  color: var(--primary);
}

/* 分类 Tab：60 × 32 r16 */
.tabs {
  position: absolute;
  left: 24px;
  top: 80px;
  display: flex;
  gap: 8px;
}

.tab {
  width: 60px;
  height: 32px;
  border-radius: 16px;
  background: var(--surface-soft);
  color: var(--ink-sub);
  font-size: 13px;
  line-height: 32px;
  text-align: center;
  transition: all 0.18s ease;
}

.tab--on {
  background: var(--primary);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(224, 120, 86, 0.22);
}

.search {
  position: absolute;
  left: 24px;
  top: 132px;
  width: 342px;
  height: 46px;
  border-radius: 23px;
  background: var(--surface);
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 18px;
  color: var(--placeholder);
  font-size: 14px;
  box-shadow: var(--shadow-card);
}

.sec {
  position: absolute;
  left: 24px;
  right: 24px;
}

.sec--recent {
  top: 206px;
}

.sec--playlists {
  top: 476px;
}

/* 列表卡片 342 × 220 r20 */
.card {
  position: absolute;
  left: 24px;
  top: 242px;
  width: 342px;
  height: 220px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 7px 0;
  overflow: hidden;
}

.crow {
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 16px;
  text-align: left;
  transition: background 0.16s ease;
}

.crow:hover {
  background: rgba(245, 239, 227, 0.62);
}

.crow__cover {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  flex: 0 0 auto;
  background-color: var(--surface-cover);
}

.crow__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.crow__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.crow__sub {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.crow__dur {
  font-size: 12px;
  color: var(--ink-sub);
  flex: 0 0 auto;
}

.crow__go {
  color: var(--placeholder);
  flex: 0 0 auto;
}

/* 我的歌单：2 × 152×116，标题 476–500，卡片从 512 起 */
.pls {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 512px;
  display: grid;
  grid-template-columns: repeat(2, 152px);
  gap: 20px 14px;
}

.pl {
  width: 152px;
  text-align: left;
  transition: transform 0.18s ease;
}

.pl:active {
  transform: scale(0.98);
}

.pl__cover {
  position: relative;
  display: block;
  width: 152px;
  height: 116px;
  border-radius: var(--r-card);
  background-color: var(--surface-cover);
  box-shadow: 0 6px 16px rgba(224, 120, 86, 0.12);
  overflow: hidden;
}

.pl__count {
  position: absolute;
  right: 10px;
  top: 10px;
  height: 20px;
  padding: 0 8px;
  border-radius: 10px;
  background: rgba(43, 31, 26, 0.34);
  color: #fff;
  font-size: 10px;
  line-height: 20px;
  backdrop-filter: blur(4px);
}

.pl__title {
  display: block;
  margin-top: 10px;
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
