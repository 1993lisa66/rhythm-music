<script setup>
import { computed, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import { api } from '@/api/client'
import { data, removeSongLocal } from '@/store/data'
import { current, playSong, state, syncPlayer } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle, fmtTime } from '@/utils/format'

/* 曲库在路由守卫里已加载完（ensureAppData），这里不需要再请求 */
const songs = computed(() => data.songs)
const ids = computed(() => songs.value.map((s) => s.id))

/* 曲库 113 首时靠滚动找歌太慢，这里做本地过滤 */
const keyword = ref('')
const visible = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return songs.value
  return songs.value.filter((s) =>
    [s.title, s.artist, s.album].some((field) => (field || '').toLowerCase().includes(kw))
  )
})

/* 删除是破坏性操作：先在面板里二次确认，确认后再调接口 */
const target = ref(null)
const removing = ref(false)

/* 多选：一次删多首，避免逐首点 */
const selecting = ref(false)
const selected = ref(new Set())
const selectedCount = computed(() => selected.value.size)

const isActive = (song) => current.value.id === song.id && state.playing
const isPicked = (song) => selected.value.has(song.id)

const play = (song) => playSong(song.id, ids.value)

const onRow = (song) => {
  if (!selecting.value) {
    play(song)
    return
  }
  const next = new Set(selected.value)
  if (next.has(song.id)) next.delete(song.id)
  else next.add(song.id)
  selected.value = next
}

const startSelect = () => {
  selecting.value = true
  selected.value = new Set()
}
const cancelSelect = () => {
  selecting.value = false
  selected.value = new Set()
}

const askRemove = (song) => {
  target.value = [song]
}
const askBatch = () => {
  if (!selectedCount.value) return
  target.value = songs.value.filter((s) => selected.value.has(s.id))
}

const closeSheet = () => {
  if (removing.value) return
  target.value = null
}

const deleteTargets = async (list) => {
  let done = 0
  const touchedCurrent = list.some((s) => s.id === current.value.id)
  for (const song of list) {
    try {
      await api.deleteSong(song.id)
      removeSongLocal(song.id)
      done += 1
    } catch (error) {
      toast(error?.message || `《${song.title}》删除失败`)
    }
  }
  if (touchedCurrent) await syncPlayer()
  return done
}

const confirmRemove = async () => {
  const list = target.value || []
  if (!list.length || removing.value) return
  removing.value = true
  try {
    const done = await deleteTargets(list)
    target.value = null
    toast(
      list.length > 1
        ? `已删除 ${done} 首歌曲及其资源`
        : `已删除《${list[0].title}》及其资源`
    )
    if (list.length > 1) cancelSelect()
  } finally {
    removing.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page__canvas songs">
      <PageNav :title="selecting ? `已选 ${selectedCount} 首` : '全部歌曲'" fallback="/library">
        <template #right>
          <template v-if="selecting">
            <button type="button" class="link" @click="cancelSelect">取消</button>
            <button
              type="button"
              class="link link--danger"
              :disabled="!selectedCount"
              @click="askBatch"
            >
              删除
            </button>
          </template>
          <button v-else type="button" class="link" @click="startSelect">选择</button>
        </template>
      </PageNav>

      <div class="filter">
        <Icon name="search" :size="15" :stroke="1.9" />
        <input
          v-model="keyword"
          class="filter__input"
          type="text"
          placeholder="在曲库里找歌名 / 歌手 / 专辑"
          aria-label="筛选曲库"
        />
        <button v-if="keyword" type="button" class="filter__clear" aria-label="清空" @click="keyword = ''">
          <Icon name="close" :size="12" :stroke="2" />
        </button>
      </div>

      <ul v-if="visible.length" class="list">
        <li v-for="song in visible" :key="song.id" class="item">
          <button type="button" class="item__main" @click="onRow(song)">
            <span v-if="selecting" class="item__check" :class="{ 'item__check--on': isPicked(song) }">
              <Icon v-if="isPicked(song)" name="check" :size="12" :stroke="2.4" />
            </span>
            <span class="item__cover" :style="coverStyle(song.cover)">
              <span v-if="isActive(song)" class="item__badge">
                <Icon name="note" :size="11" :stroke="2" />
              </span>
            </span>
            <span class="item__text">
              <span class="item__title" :class="{ 'item__title--on': current.id === song.id }">
                {{ song.title }}
              </span>
              <span class="item__sub">{{ song.artist }} · {{ song.album }}</span>
            </span>
            <span class="item__dur num">{{ fmtTime(song.duration) }}</span>
          </button>
          <button
            v-if="!selecting"
            type="button"
            class="item__del"
            :aria-label="`删除 ${song.title}`"
            @click="askRemove(song)"
          >
            <Icon name="trash" :size="17" :stroke="1.7" />
          </button>
        </li>
      </ul>

      <p v-if="visible.length" class="tip">
        <template v-if="selecting">点曲目勾选，可一次删除多首</template>
        <template v-else-if="keyword">找到 {{ visible.length }} 首，点「选择」可批量删除</template>
        <template v-else>共 {{ songs.length }} 首，点击播放，右侧可删除歌曲资源</template>
      </p>

      <div v-else class="empty">
        <span class="empty__icon"><Icon name="search" :size="24" :stroke="1.6" /></span>
        <p class="empty__title">没有匹配的歌曲</p>
        <p class="empty__sub">换个关键词试试，或清空筛选看全部</p>
        <button type="button" class="empty__btn" @click="keyword = ''">清空筛选</button>
      </div>
    </div>

    <ActionSheet
      :open="!!target"
      :title="target && target.length > 1 ? `删除 ${target.length} 首歌曲？` : '删除歌曲资源？'"
      :subtitle="
        target
          ? target.length > 1
            ? '将从曲库移除这些歌曲，并删除各自的音频与封面文件，无法恢复'
            : `将从曲库移除《${target[0].title}》，并删除音频与封面文件，无法恢复`
          : ''
      "
      :actions="[{ key: 'confirm', label: '确认删除', icon: 'trash', danger: true }]"
      cancel-text="保留歌曲"
      @pick="confirmRemove"
      @close="closeSheet"
    />
  </div>
</template>

<style scoped>
.songs {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 150px;
}

.link {
  font-size: 13px;
  line-height: 22px;
  /* 22 + 上下各 11 = 44px 最小热区，视觉位置不变 */
  padding: 11px 12px;
  margin: -11px -12px;
  color: var(--ink-sub);
  transition: color 0.16s ease;
}

.link:hover {
  color: var(--primary);
}

.link--danger {
  color: #c4543f;
  font-weight: 600;
}

.link--danger:disabled {
  color: var(--placeholder);
}

.filter {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  margin-bottom: 14px;
  padding: 0 12px;
  border-radius: var(--r-btn);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  color: var(--placeholder);
}

.filter__input {
  flex: 1 1 auto;
  min-width: 0;
  height: 100%;
  font-size: 14px;
  color: var(--ink);
}

.filter__input::placeholder {
  color: var(--placeholder);
}

.filter__clear {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  color: var(--placeholder);
}

.list {
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 6px 0;
  overflow: hidden;
}

.item {
  display: flex;
  align-items: center;
}

.item__main {
  flex: 1 1 auto;
  min-width: 0;
  height: 62px;
  padding: 0 6px 0 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  transition: background 0.16s ease;
}

.item__main:hover {
  background: rgba(245, 239, 227, 0.42);
}

.item__check {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
  border-radius: 50%;
  border: 1.5px solid rgba(43, 31, 26, 0.18);
  display: grid;
  place-items: center;
  color: #fff;
  transition: background 0.16s ease, border-color 0.16s ease;
}

.item__check--on {
  background: var(--primary);
  border-color: var(--primary);
}

.item__cover {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 11px;
  background-color: var(--surface-cover);
  flex: 0 0 auto;
}

.item__badge {
  position: absolute;
  right: -3px;
  bottom: -3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 2px 6px rgba(224, 120, 86, 0.4);
}

.item__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.item__title {
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item__title--on {
  color: var(--primary);
}

.item__sub {
  font-size: 11px;
  line-height: 14px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item__dur {
  font-size: 12px;
  color: var(--ink-sub);
  flex: 0 0 auto;
  margin-right: 2px;
}

.item__del {
  width: 44px;
  height: 62px;
  display: grid;
  place-items: center;
  color: var(--placeholder);
  flex: 0 0 auto;
  transition: color 0.16s ease;
}

.item__del:hover {
  color: var(--primary);
}

.tip {
  margin-top: 22px;
  font-size: 12px;
  line-height: 17px;
  color: var(--placeholder);
  text-align: center;
}

.empty {
  margin-top: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty__icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  margin-bottom: 4px;
}

.empty__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-sub);
}

.empty__sub {
  font-size: 12px;
  color: var(--placeholder);
}

.empty__btn {
  margin-top: 6px;
  height: 34px;
  padding: 0 16px;
  border-radius: var(--r-btn);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
}
</style>
