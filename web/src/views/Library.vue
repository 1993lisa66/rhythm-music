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
import { coverStyle, fmtSpan } from '@/utils/format'

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

/* 列表区标题跟随当前 tab，并带上数量，避免和 tab 标签重复报同一个词 */
const listTitle = computed(() => {
  if (activeTab.value === '歌曲') return `全部 ${songRows.value.length} 首`
  if (activeTab.value === '歌单') return `我的歌单 ${playlistRows.value.length} 个`
  if (activeTab.value === '专辑') return `全部专辑 ${albumRows.value.length} 张`
  return library.value.recent.title
})
/* 歌曲 tab 本身已经是全量列表，「全部」入口没有新内容，不再显示 */
const moreLabel = computed(() => (activeTab.value === '歌曲' ? '' : library.value.recent.more))

/* 「全部 ›」按当前 tab 分流：歌曲 → 全部歌曲、歌单 → 我的歌单、专辑 → 全部专辑 */
const MORE_ROUTES = { 歌曲: '/songs', 歌单: '/mylists', 专辑: '/albums' }
const openMore = () => router.push(MORE_ROUTES[activeTab.value] || '/songs')

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

/* 歌曲列表分页：默认只渲染 20 首，滚动到底部再追加一页 */
const PAGE_SIZE = 20
const visibleCount = ref(PAGE_SIZE)
const pageSongs = computed(() => songRows.value.slice(0, visibleCount.value))
const hasMore = computed(() => visibleCount.value < songRows.value.length)
const pageEl = ref(null)

const loadMore = () => {
  if (!hasMore.value) return
  visibleCount.value = Math.min(visibleCount.value + PAGE_SIZE, songRows.value.length)
}

/* 滚动到距底部 200px 时加载下一页；只有歌曲 tab 需要分页 */
const onScroll = (e) => {
  if (activeTab.value !== '歌曲' || !hasMore.value) return
  const el = e.currentTarget
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 200) loadMore()
}

const songIds = computed(() => songRows.value.map((s) => s.id))
const playlistRows = computed(() => library.value.playlists.items)
/* 专辑视图直接用 /library/albums 的聚合结果，避免前端再猜分组口径 */
const albumRows = computed(() => data.albums || [])

/* 固定 800px 画布会把长列表截断，按实际行数撑开整个滚动区 */
const rowCount = computed(() => {
  if (activeTab.value === '歌曲') return pageSongs.value.length
  if (activeTab.value === '歌单') return playlistRows.value.length
  return albumRows.value.length
})
/* 卡片高度跟随实际行数（60 一行 + 上下 7px 内边距），不预留空白 */
const cardHeight = computed(() => Math.max(74, rowCount.value * 60 + 14))
/* 画布高度按卡片实际高度撑开；底部留白交给 base.css 的 .page::after 统一处理 */
const canvasHeight = computed(() => Math.max(800, 242 + cardHeight.value))

const isRowActive = (song) => current.value.id === song.id && state.playing

const playRow = (song) => playSong(song.id, songIds.value)
const openPlaylist = (p) => router.push(`/playlist/${p.id}`)
/* 专辑改成进详情页，才能看到合集简介与曲目列表 */
const openAlbum = (album) => {
  if (album?.name) router.push(`/album/${encodeURIComponent(album.name)}`)
}

/* 切换 tab：重置分页并回到顶部，避免停在旧位置立即触发加载 */
const selectTab = (t) => {
  if (t === activeTab.value) return
  tab.value = t
  visibleCount.value = PAGE_SIZE
  if (pageEl.value) pageEl.value.scrollTop = 0
}

const pickSort = (key) => {
  sortKey.value = key
  visibleCount.value = PAGE_SIZE
  if (pageEl.value) pageEl.value.scrollTop = 0
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
  <div class="page" ref="pageEl" @scroll.passive="onScroll">
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
          @click="selectTab(t)"
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
        :title="listTitle"
        :more="moreLabel"
        @more="openMore"
      />

      <div class="card" :style="{ height: `${cardHeight}px` }">
        <template v-if="activeTab === '歌曲'">
          <SongRow
            v-for="song in pageSongs"
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
            @click="openAlbum(a)"
          >
            <span class="crow__cover" :style="coverStyle(a.cover)"></span>
            <span class="crow__text">
              <span class="crow__title">{{ a.name }}</span>
              <span class="crow__sub">{{ a.artist }} · {{ a.songCount }} 首</span>
            </span>
            <span class="crow__dur num">{{ fmtSpan(a.duration) }}</span>
          </button>
        </template>
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
  right: 24px;
  top: 132px;
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

/* 列表卡片：左右各留 24，随屏宽自适应 */
.card {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 242px;
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

</style>
