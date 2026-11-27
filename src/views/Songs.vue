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
/* 删除是破坏性操作：先在面板里二次确认，确认后再调接口 */
const target = ref(null)
const removing = ref(false)

const isActive = (song) => current.value.id === song.id && state.playing

const play = (song) => playSong(song.id, ids.value)

const askRemove = (song) => {
  target.value = song
}

const closeSheet = () => {
  if (removing.value) return
  target.value = null
}

const confirmRemove = async () => {
  const song = target.value
  if (!song || removing.value) return
  removing.value = true
  try {
    await api.deleteSong(song.id)
    removeSongLocal(song.id)
    target.value = null
    toast(`已删除《${song.title}》及其资源`)
    /* 当前正在播的歌曲被删掉时要让播放器换歌，否则会停在无效曲目上 */
    if (current.value.id === song.id) await syncPlayer()
  } catch (error) {
    toast(error?.message || '删除失败')
  } finally {
    removing.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page__canvas songs">
      <PageNav title="全部歌曲" fallback="/library">
        <template #right>
          <span class="count num">{{ songs.length }} 首</span>
        </template>
      </PageNav>

      <ul v-if="songs.length" class="list">
        <li v-for="song in songs" :key="song.id" class="item">
          <button type="button" class="item__main" @click="play(song)">
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
            type="button"
            class="item__del"
            :aria-label="`删除 ${song.title}`"
            @click="askRemove(song)"
          >
            <Icon name="trash" :size="17" :stroke="1.7" />
          </button>
        </li>
      </ul>

      <p v-if="songs.length" class="tip">共 {{ songs.length }} 首，点击播放，右侧可删除歌曲资源</p>

      <div v-else class="empty">
        <span class="empty__icon"><Icon name="note" :size="24" :stroke="1.6" /></span>
        <p class="empty__title">曲库还是空的</p>
        <p class="empty__sub">导入歌曲后会出现在这里</p>
      </div>
    </div>

    <ActionSheet
      :open="!!target"
      title="删除歌曲资源？"
      :subtitle="
        target
          ? `将从曲库移除《${target.title}》，并删除音频与封面文件，无法恢复`
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

.count {
  font-size: 13px;
  line-height: 22px;
  color: var(--ink-sub);
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
  transition: background 0.16s ease;
}

.item__main:hover {
  background: rgba(245, 239, 227, 0.42);
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
</style>
