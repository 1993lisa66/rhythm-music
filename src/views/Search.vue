<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import SongRow from '@/components/SongRow.vue'
import { api } from '@/api/client'
import { data, refreshHot, refreshRecommend } from '@/store/data'
import { current, playSong, state } from '@/store/player'
import { coverStyle } from '@/utils/format'
import { goBack } from '@/utils/nav'

const router = useRouter()
const route = useRoute()

const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const inputRef = ref(null)

const EMPTY_HOT = { title: '热门搜索', refresh: '换一换', placeholder: '搜索你喜欢的音乐', cancel: '取消', items: [] }
const hot = computed(() => data.hot || EMPTY_HOT)
const hotItems = computed(() => hot.value.items)
const recommend = computed(() => data.recommend || { title: '猜你喜欢', items: [] })

const TONE = {
  primary: 'var(--primary)',
  sage: 'var(--sage)',
  honey: 'var(--honey)',
  plum: 'var(--plum)'
}

/**
 * 搜索走后端 /search（歌名 / 歌手 / 专辑 / 流派都能命中）。
 * 用请求序号丢弃过期响应，避免快速输入时旧结果覆盖新结果。
 */
const results = ref([])
const artists = ref([])
const playlists = ref([])
const searching = ref(false)
let seq = 0

const hasResult = computed(
  () => results.value.length + artists.value.length + playlists.value.length > 0
)

const normalize = (q) => q.replace(/(系|音乐|歌曲)$/g, '')

async function runSearch(keyword) {
  const mine = ++seq
  searching.value = true
  try {
    let payload = await api.search({ q: keyword, limit: 30 })
    if (mine !== seq) return
    const loose = normalize(keyword)
    // 关键词带「系 / 音乐」这类后缀时命中率低，退一步再搜一次
    if (!payload.songs?.length && !payload.artists?.length && !payload.playlists?.length && loose && loose !== keyword) {
      payload = await api.search({ q: loose, limit: 30 })
      if (mine !== seq) return
    }
    results.value = payload.songs || []
    artists.value = payload.artists || []
    playlists.value = payload.playlists || []
    if (results.value.length || artists.value.length || playlists.value.length) pushHistory(keyword)
    // 关键词写进地址栏：刷新 / 返回都能还原这次搜索结果
    router.replace({ query: { q: keyword } })
  } catch {
    if (mine === seq) {
      results.value = []
      artists.value = []
      playlists.value = []
    }
  } finally {
    if (mine === seq) searching.value = false
  }
}

/* 搜索历史：本地存最近 8 条，点一下就能重搜 */
const HISTORY_KEY = 'rhythm.searchHistory'
const history = ref([])
const readHistory = () => {
  try {
    history.value = JSON.parse(window.localStorage.getItem(HISTORY_KEY) || '[]').slice(0, 8)
  } catch {
    history.value = []
  }
}
const pushHistory = (word) => {
  const next = [word, ...history.value.filter((w) => w !== word)].slice(0, 8)
  history.value = next
  try {
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
  } catch {
    /* 隐私模式下写不进去也不影响搜索 */
  }
}
const clearHistory = () => {
  history.value = []
  try {
    window.localStorage.removeItem(HISTORY_KEY)
  } catch {
    /* 忽略 */
  }
}
const useHistory = (word) => {
  query.value = word
  inputRef.value?.focus()
}

const hasQuery = computed(() => query.value.trim().length > 0)
const bigCards = computed(() => recommend.value.items.filter((i) => i.size === 'lg'))
const smallCards = computed(() => recommend.value.items.filter((i) => i.size !== 'lg'))

const cancel = () => {
  if (query.value) query.value = ''
  else goBack(router, '/discover')
}

const pickHot = (item) => {
  query.value = item.text
  inputRef.value?.focus()
}

const rotateHot = async () => {
  try {
    data.hot = await api.refreshHot()
  } catch {
    /* 换一换热词失败不影响已展示的词 */
  }
}

const playRecommend = (item) => playSong(item.id)
const playResult = (song) => playSong(song.id, results.value.map((s) => s.id))
const playAllResults = () => {
  if (results.value.length) playSong(results.value[0].id, results.value.map((s) => s.id))
}
const openArtist = (name) => router.push(`/artist/${encodeURIComponent(name)}`)
const openPlaylist = (id) => router.push(`/playlist/${id}`)

onMounted(async () => {
  readHistory()
  // 带 q 的深链直接出结果，否则刷新/分享进来会停在空态
  const initial = (route.query.q || '').toString().trim()
  if (initial) runSearch(initial)
  if (route.query.q) inputRef.value?.focus()
  try {
    await Promise.all([refreshHot(), refreshRecommend()])
  } catch {
    /* 热词 / 推荐失败时页面仍可搜索 */
  }
})

/* 输入即搜：250ms 去抖，空关键词清空结果 */
let searchTimer = null
watch(query, (value) => {
  const keyword = value.trim()
  if (searchTimer) window.clearTimeout(searchTimer)
  if (!keyword) {
    seq += 1
    results.value = []
    artists.value = []
    playlists.value = []
    searching.value = false
    return
  }
  searchTimer = window.setTimeout(() => runSearch(keyword), 250)
})

/* 支持带 q 的深链，且在已打开搜索页时同步关键词 */
watch(
  () => route.query.q,
  (q) => {
    if (typeof q === 'string' && q !== query.value) query.value = q
  }
)
</script>

<template>
  <div class="page">
    <div class="page__canvas">
      <div class="sbox">
        <Icon name="search" :size="16" :stroke="1.9" />
        <input
          ref="inputRef"
          v-model="query"
          class="sbox__input"
          type="text"
          inputmode="search"
          enterkeyhint="search"
          :placeholder="hot.placeholder"
          aria-label="搜索音乐"
        />
        <button v-if="query" type="button" class="sbox__clear" aria-label="清空" @click="query = ''">
          <Icon name="close" :size="13" :stroke="2" />
        </button>
      </div>

      <button type="button" class="cancel" @click="cancel">{{ hot.cancel }}</button>

      <template v-if="!hasQuery">
        <div class="browse">
          <div v-if="history.length" class="history">
            <div class="sec">
              <h2 class="sec__title">搜索历史</h2>
              <button type="button" class="sec__more" @click="clearHistory">清空</button>
            </div>
            <div class="hchips">
              <button
                v-for="word in history"
                :key="word"
                type="button"
                class="hchip"
                @click="useHistory(word)"
              >
                {{ word }}
              </button>
            </div>
          </div>

          <div class="sec sec--hot">
            <h2 class="sec__title">{{ hot.title }}</h2>
            <button type="button" class="sec__more" @click="rotateHot">{{ hot.refresh }}</button>
          </div>

          <div class="chips">
            <button
              v-for="item in hotItems"
              :key="item.text"
              type="button"
              class="chip"
              :style="{ background: TONE[item.tone] }"
              @click="pickHot(item)"
            >
              {{ item.text }}
            </button>
          </div>

          <h2 class="sec sec--rec">{{ recommend.title }}</h2>

          <div class="rec">
            <div class="rec__row rec__row--lg">
              <button
                v-for="item in bigCards"
                :key="item.id"
                type="button"
                class="rcard"
                @click="playRecommend(item)"
              >
                <span class="rcard__cover rcard__cover--lg" :style="coverStyle(item.cover)"></span>
                <span class="rcard__title">{{ item.title }}</span>
                <span class="rcard__sub">{{ item.sub }}</span>
              </button>
            </div>

            <div class="rec__row rec__row--sm">
              <button
                v-for="item in smallCards"
                :key="item.id"
                type="button"
                class="rcard"
                @click="playRecommend(item)"
              >
                <span class="rcard__cover rcard__cover--sm" :style="coverStyle(item.cover)"></span>
                <span class="rcard__title">{{ item.title }}</span>
                <span v-if="item.sub" class="rcard__sub">{{ item.sub }}</span>
              </button>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="results">
          <template v-if="hasResult">
            <section v-if="artists.length" class="rgroup">
              <h2 class="rgroup__title">歌手</h2>
              <div class="artists">
                <button
                  v-for="a in artists"
                  :key="a.name"
                  type="button"
                  class="acard"
                  @click="openArtist(a.name)"
                >
                  <span class="acard__cover" :style="coverStyle(a.cover)"></span>
                  <span class="acard__name">{{ a.name }}</span>
                  <span class="acard__sub num">{{ a.songCount }} 首</span>
                </button>
              </div>
            </section>

            <section v-if="playlists.length" class="rgroup">
              <h2 class="rgroup__title">歌单</h2>
              <div class="rlist">
                <button
                  v-for="p in playlists"
                  :key="p.id"
                  type="button"
                  class="prow"
                  @click="openPlaylist(p.id)"
                >
                  <span class="prow__cover" :style="coverStyle(p.cover)"></span>
                  <span class="prow__text">
                    <span class="prow__title">{{ p.title }}</span>
                    <span class="prow__sub num">{{ p.count }} 首 · {{ p.durationText }}</span>
                  </span>
                  <Icon class="prow__go" name="chevron" :size="14" :stroke="1.8" />
                </button>
              </div>
            </section>

            <section v-if="results.length" class="rgroup">
              <div class="rgroup__head">
                <h2 class="rgroup__title">
                  歌曲 <span class="num">{{ results.length }}</span> 首
                </h2>
                <button type="button" class="rgroup__play" @click="playAllResults">
                  <Icon name="play" :size="11" />
                  <span>播放全部</span>
                </button>
              </div>
              <div class="rlist">
                <SongRow
                  v-for="song in results"
                  :key="song.id"
                  :song="song"
                  :active="current.id === song.id && state.playing"
                  @select="playResult"
                />
              </div>
            </section>
          </template>

          <div v-else-if="!searching" class="empty">
          <span class="empty__icon"><Icon name="search" :size="26" :stroke="1.6" /></span>
          <p class="empty__title">没有找到「{{ query }}」相关的音乐</p>
            <p class="empty__sub">换个关键词，或者试试热门搜索</p>
            <button type="button" class="empty__btn" @click="query = ''">清空重搜</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* 搜索框 300 × 48 */
.sbox {
  position: absolute;
  left: 24px;
  top: 30px;
  width: 300px;
  height: 48px;
  border-radius: var(--r-btn);
  background: var(--surface);
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 16px;
  color: var(--placeholder);
  box-shadow: 0 2px 10px rgba(224, 120, 86, 0.06);
  transition: box-shadow 0.2s ease;
}

.sbox:focus-within {
  box-shadow: 0 0 0 2px rgba(224, 120, 86, 0.22);
}

.sbox__input {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 14px;
  line-height: 18px;
  color: var(--ink);
}

.sbox__input::placeholder {
  color: var(--placeholder);
}

.sbox__clear {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--ink-sub);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}

.cancel {
  position: absolute;
  right: 24px;
  top: 30px;
  height: 48px;
  font-size: 15px;
  line-height: 48px;
  color: var(--primary);
  padding-left: 8px;
}

.sec {
  position: absolute;
  left: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 24px;
}

/* 浏览态整块从搜索框下方开始，内部用文档流依次排列，热搜换行时下方自动跟随 */
.browse {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 114px;
}

.sec--hot,
.sec--rec {
  position: relative;
  top: auto;
  left: auto;
  right: auto;
}

.sec--rec {
  margin-top: 26px;
}

.sec__title {
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
  color: var(--ink);
}

.sec__more {
  font-size: 13px;
  line-height: 18px;
  color: var(--primary);
  padding: 4px 0 4px 10px;
}

/* 搜索历史：与热搜区分开，用浅色描边胶囊 */
.history {
  margin-bottom: 24px;
}

.history .sec {
  position: relative;
  top: auto;
  left: auto;
  right: auto;
}

.hchips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.hchip {
  height: 32px;
  max-width: 100%;
  padding: 0 14px;
  border-radius: var(--r-chip);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  font-size: 13px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  transition: color 0.16s ease, transform 0.16s ease;
}

.hchip:hover {
  color: var(--primary);
}

.hchip:active {
  transform: scale(0.96);
}

/* 热搜 Chip：36 高 r18，自动换行 */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.chip {
  height: 36px;
  padding: 0 25px;
  border-radius: var(--r-chip);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
  transition: transform 0.16s ease, filter 0.16s ease;
}

.chip:hover {
  filter: brightness(1.04);
}

.chip:active {
  transform: scale(0.95);
}

/* 猜你喜欢 */
.rec {
  margin-top: 16px;
}

.rec__row {
  display: flex;
  gap: 14px;
  /* 卡片数量变化时允许横向滑动，避免撑出设备外壳 */
  overflow-x: auto;
  scrollbar-width: none;
  overscroll-behavior-x: contain;
}

.rec__row::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.rec__row .rcard {
  flex: 0 0 152px;
}

.rec__row--sm {
  margin-top: 16px;
}

.rcard {
  width: 152px;
  text-align: left;
}

.rcard__cover {
  display: block;
  border-radius: var(--r-card);
  background-color: var(--surface-cover);
  box-shadow: 0 6px 16px rgba(224, 120, 86, 0.12);
  transition: transform 0.18s ease;
}

.rcard:hover .rcard__cover {
  transform: translateY(-2px);
}

.rcard__cover--lg {
  width: 152px;
  height: 152px;
}

.rcard__cover--sm {
  width: 152px;
  height: 116px;
}

.rcard__title {
  display: block;
  margin-top: 8px;
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.rcard__sub {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 搜索结果 */
/* 结果区：歌手 / 歌单 / 歌曲 三组共用一个滚动容器 */
.results {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 114px;
  bottom: 100px;
  overflow-y: auto;
  scrollbar-width: none;
}

.results::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.rgroup {
  margin-bottom: 20px;
}

.rgroup__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 4px 8px;
}

.rgroup__title {
  margin: 0 0 8px 4px;
  font-size: 13px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink-sub);
}

.rgroup__head .rgroup__title {
  margin: 0;
}

.rgroup__play {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
}

/* 歌手：横向圆形头像 */
.artists {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding: 2px 4px 6px;
  scrollbar-width: none;
}

.artists::-webkit-scrollbar {
  height: 0;
}

.acard {
  flex: 0 0 auto;
  width: 78px;
  text-align: center;
}

.acard__cover {
  display: block;
  width: 78px;
  height: 78px;
  border-radius: 50%;
  background-color: var(--surface-cover);
  box-shadow: 0 6px 14px rgba(43, 31, 26, 0.1);
}

.acard__name {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  font-weight: 600;
  line-height: 16px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.acard__sub {
  display: block;
  font-size: 11px;
  line-height: 14px;
  color: var(--ink-sub);
}

.rlist {
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 6px 0;
  overflow: hidden;
}

/* 歌单行与音乐库列表同规格 */
.prow {
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 16px;
  text-align: left;
  transition: background 0.16s ease;
}

.prow:hover {
  background: rgba(245, 239, 227, 0.6);
}

.prow__cover {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  flex: 0 0 auto;
  background-color: var(--surface-cover);
}

.prow__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.prow__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.prow__sub {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
}

.prow__go {
  color: var(--placeholder);
  flex: 0 0 auto;
}

/* 空状态 */
.empty {
  margin-top: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.empty__icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--honey);
  display: grid;
  place-items: center;
  margin-bottom: 4px;
}

.empty__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 20px;
  color: var(--ink);
}

.empty__sub {
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-sub);
}

.empty__btn {
  margin-top: 10px;
  height: 40px;
  padding: 0 22px;
  border-radius: 20px;
  border: 1.5px solid var(--primary);
  color: var(--primary);
  font-size: 14px;
  font-weight: 600;
  background: var(--surface);
}
</style>
