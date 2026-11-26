<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import SongRow from '@/components/SongRow.vue'
import search from '@/data/search.json'
import { current, playSong, searchSongs, state } from '@/store/player'
import { coverStyle } from '@/utils/format'

const router = useRouter()
const route = useRoute()

const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const inputRef = ref(null)
const hotItems = ref(search.hot.items.slice())

const TONE = {
  primary: 'var(--primary)',
  sage: 'var(--sage)',
  honey: 'var(--honey)',
  plum: 'var(--plum)'
}

const normalize = (q) => q.replace(/(系|音乐|歌曲)$/g, '')
const results = computed(() => {
  const q = query.value.trim()
  if (!q) return []
  const direct = searchSongs(q)
  return direct.length ? direct : searchSongs(normalize(q))
})
const hasQuery = computed(() => query.value.trim().length > 0)
const recommend = search.recommend.items
const bigCards = recommend.filter((i) => i.size === 'lg')
const smallCards = recommend.filter((i) => i.size !== 'lg')

const cancel = () => {
  if (query.value) query.value = ''
  else router.back()
}

const pickHot = (item) => {
  query.value = item.text
  inputRef.value?.focus()
}

const refreshHot = () => {
  hotItems.value = [...hotItems.value.slice(1), hotItems.value[0]]
}

const playRecommend = (item) => playSong(item.id)
const playResult = (song) => playSong(song.id, results.value.map((s) => s.id))

onMounted(() => {
  if (route.query.q) inputRef.value?.focus()
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
          :placeholder="search.placeholder"
          aria-label="搜索音乐"
        />
        <button v-if="query" type="button" class="sbox__clear" aria-label="清空" @click="query = ''">
          <Icon name="close" :size="13" :stroke="2" />
        </button>
      </div>

      <button type="button" class="cancel" @click="cancel">{{ search.cancel }}</button>

      <template v-if="!hasQuery">
        <div class="sec sec--hot">
          <h2 class="sec__title">{{ search.hot.title }}</h2>
          <button type="button" class="sec__more" @click="refreshHot">{{ search.hot.refresh }}</button>
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

        <h2 class="sec sec--rec">{{ search.recommend.title }}</h2>

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
      </template>

      <template v-else>
        <p class="rlabel">
          搜索结果 <span class="num">{{ results.length }}</span> 首
        </p>

        <div v-if="results.length" class="rlist">
          <SongRow
            v-for="song in results"
            :key="song.id"
            :song="song"
            :active="current.id === song.id && state.playing"
            @select="playResult"
          />
        </div>

        <div v-else class="empty">
          <span class="empty__icon"><Icon name="search" :size="26" :stroke="1.6" /></span>
          <p class="empty__title">没有找到「{{ query }}」相关的音乐</p>
          <p class="empty__sub">换个关键词，或者试试热门搜索</p>
          <button type="button" class="empty__btn" @click="query = ''">清空重搜</button>
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

.sec--hot {
  top: 114px;
}

.sec--rec {
  top: 272px;
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

/* 热搜 Chip：36 高 r18 */
.chips {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 154px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 10px;
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
  position: absolute;
  left: 24px;
  right: 24px;
  top: 312px;
}

.rec__row {
  display: flex;
  gap: 14px;
}

.rec__row--sm {
  position: absolute;
  left: 0;
  right: 0;
  top: 200px;
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
.rlabel {
  position: absolute;
  left: 24px;
  top: 114px;
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-sub);
}

.rlist {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 152px;
  max-height: 500px;
  overflow-y: auto;
  scrollbar-width: none;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 6px 0;
}

.rlist::-webkit-scrollbar {
  width: 0;
}

/* 空状态 */
.empty {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 300px;
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
