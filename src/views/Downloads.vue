<script setup>
import { computed, ref } from 'vue'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import downloads from '@/data/downloads.json'
import { current, getSong, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const list = ref(
  downloads.tracks
    .map((t) => {
      const song = getSong(t.id)
      return song ? { ...song, size: t.size } : null
    })
    .filter(Boolean)
)

const editing = ref(false)

const totalSize = computed(() =>
  list.value.reduce((sum, s) => sum + (Number.parseFloat(s.size) || 0), 0).toFixed(1)
)

const ids = computed(() => list.value.map((s) => s.id))

const play = (song) => playSong(song.id, ids.value)

const toggleEdit = () => {
  if (!list.value.length) return
  editing.value = !editing.value
}

const remove = (song) => {
  list.value = list.value.filter((s) => s.id !== song.id)
  if (!list.value.length) editing.value = false
  toast(`已删除「${song.title}」`)
}

const removeAll = () => {
  list.value = []
  editing.value = false
  toast('已删除全部离线歌曲')
}
</script>

<template>
  <div class="page">
    <div class="page__canvas downloads">
      <PageNav title="离线下载" fallback="/profile">
        <template #right>
          <button type="button" class="edit" :disabled="!list.length" @click="toggleEdit">
            {{ editing ? '完成' : '编辑' }}
          </button>
        </template>
      </PageNav>

      <div class="summary">
        <span class="summary__cover">
          <Icon name="folder" :size="26" :stroke="1.7" />
        </span>
        <span class="summary__text">
          <span class="summary__title">已下载 {{ list.length }} 首</span>
          <span class="summary__sub num">共 {{ totalSize }} MB · 仅 Wi-Fi 下载</span>
        </span>
      </div>

      <ul v-if="list.length" class="list">
        <li v-for="song in list" :key="song.id" class="item">
          <button type="button" class="item__main" @click="play(song)">
            <span class="item__cover" :style="coverStyle(song.cover)">
              <span v-if="current.id === song.id && state.playing" class="item__badge">
                <Icon name="note" :size="12" :stroke="2" />
              </span>
            </span>
            <span class="item__text">
              <span class="item__title" :class="{ 'item__title--on': current.id === song.id }">
                {{ song.title }}
              </span>
              <span class="item__sub">{{ song.artist }} · {{ song.size }}</span>
            </span>
          </button>
          <button
            v-if="editing"
            type="button"
            class="item__del"
            :aria-label="`删除 ${song.title}`"
            @click="remove(song)"
          >
            <Icon name="trash" :size="17" :stroke="1.8" />
          </button>
        </li>
      </ul>

      <div v-else class="empty">
        <span class="empty__icon"><Icon name="download" :size="26" :stroke="1.6" /></span>
        <p class="empty__title">还没有离线歌曲</p>
        <p class="empty__sub">在歌单里点击下载，没网也能听</p>
      </div>

      <button v-if="editing" type="button" class="danger" @click="removeAll">删除全部</button>
    </div>
  </div>
</template>

<style scoped>
.downloads {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 140px;
}

.edit {
  font-size: 13px;
  color: var(--primary);
}

.edit:disabled {
  color: var(--placeholder);
  cursor: default;
}

/* 概览卡 342 × 76 */
.summary {
  width: 100%;
  height: 76px;
  padding: 0 16px;
  border-radius: var(--r-card);
  background: var(--sunset-soft);
  display: flex;
  align-items: center;
  gap: 14px;
}

.summary__cover {
  width: 44px;
  height: 44px;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.55);
  color: var(--primary);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}

.summary__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.summary__title {
  font-size: 15px;
  font-weight: 700;
  line-height: 19px;
  color: var(--ink);
}

.summary__sub {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink);
  opacity: 0.62;
}

.list {
  margin-top: 16px;
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

.item + .item {
  box-shadow: inset 0 1px 0 rgba(43, 31, 26, 0.045);
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

.item__del {
  width: 46px;
  height: 62px;
  display: grid;
  place-items: center;
  color: #c4543f;
  flex: 0 0 auto;
}

.empty {
  margin-top: 60px;
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
  margin-bottom: 6px;
}

.empty__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}

.empty__sub {
  font-size: 12px;
  color: var(--ink-sub);
}

.danger {
  width: 100%;
  height: 48px;
  margin-top: 16px;
  border-radius: var(--r-btn);
  background: rgba(196, 84, 63, 0.1);
  color: #c4543f;
  font-size: 14px;
  font-weight: 600;
}
</style>
