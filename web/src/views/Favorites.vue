<script setup>
import { computed, onMounted } from 'vue'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import { api } from '@/api/client'
import { data, refreshFavorites } from '@/store/data'
import { current, playSong, state, syncLiked } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle, fmtSpan, fmtTime } from '@/utils/format'

const list = computed(() => data.favorites?.items || [])
const ids = computed(() => list.value.map((s) => s.id))
const total = computed(() => list.value.length)

const spanText = computed(() => {
  const seconds = list.value.reduce((sum, s) => sum + (Number(s.duration) || 0), 0)
  return fmtSpan(seconds)
})

const play = (song) => playSong(song.id, ids.value)
const playAll = () => {
  if (ids.value.length) playSong(ids.value[0], ids.value)
}

/* 取消收藏后立刻从列表里移除，避免「还在列表里但心是空的」这种不一致 */
const unfavorite = async (song) => {
  try {
    const payload = await api.toggleFavorite(song.id)
    syncLiked(song.id, payload.liked)
    await refreshFavorites()
    toast(payload.liked ? `已重新收藏「${song.title}」` : `已取消收藏「${song.title}」`)
  } catch (error) {
    toast(error?.message || '操作失败')
  }
}

onMounted(async () => {
  try {
    await refreshFavorites()
  } catch (error) {
    toast(error?.message || '加载收藏失败')
  }
})
</script>

<template>
  <div class="page">
    <div class="page__canvas favorites">
      <PageNav title="我的收藏" fallback="/profile">
        <template #right>
          <span class="count num">{{ total }} 首</span>
        </template>
      </PageNav>

      <button type="button" class="summary" :disabled="!total" @click="playAll">
        <span class="summary__icon">
          <Icon name="heart" :size="22" :stroke="1.7" :filled="total > 0" />
        </span>
        <span class="summary__text">
          <span class="summary__title num">共 {{ total }} 首</span>
          <span class="summary__sub num">{{ spanText }} · 点此全部播放</span>
        </span>
        <span class="summary__play">
          <Icon name="play" :size="15" />
        </span>
      </button>

      <ul v-if="total" class="list">
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
              <span class="item__sub">{{ song.artist }} · {{ song.album }}</span>
            </span>
            <span class="item__dur num">{{ fmtTime(song.duration) }}</span>
          </button>
          <button
            type="button"
            class="item__heart hit"
            :aria-label="`取消收藏 ${song.title}`"
            @click="unfavorite(song)"
          >
            <Icon name="heart" :size="17" :stroke="1.8" filled />
          </button>
        </li>
      </ul>

      <div v-else class="empty">
        <span class="empty__icon"><Icon name="heart" :size="26" :stroke="1.6" /></span>
        <p class="empty__title">还没有收藏歌曲</p>
        <p class="empty__sub">在播放页点一下心形，就会出现在这里</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.favorites {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 140px;
}

.count {
  font-size: 13px;
  line-height: 22px;
  color: var(--ink-sub);
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
  text-align: left;
}

.summary:disabled {
  cursor: default;
}

.summary__icon {
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
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.summary__play {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  box-shadow: 0 4px 12px rgba(224, 120, 86, 0.32);
}

.summary__play :deep(.ico) {
  transform: translateX(1px);
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

.item__dur {
  font-size: 12px;
  color: var(--ink-sub);
  flex: 0 0 auto;
  margin-right: 4px;
}

.item__heart {
  width: 46px;
  height: 62px;
  display: grid;
  place-items: center;
  color: var(--primary);
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
</style>
