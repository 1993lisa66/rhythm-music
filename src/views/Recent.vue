<script setup>
import { computed, onMounted } from 'vue'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import { api } from '@/api/client'
import { data, refreshRecent } from '@/store/data'
import { current, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle, fmtTime } from '@/utils/format'

const groups = computed(() =>
  (data.recent?.groups || [])
    .map((g) => ({ label: g.label, songs: g.items }))
    .filter((g) => g.songs.length)
)

const allIds = computed(() => groups.value.flatMap((g) => g.songs.map((s) => s.id)))
const total = computed(() => allIds.value.length)
const hoursText = computed(() => {
  const seconds = groups.value
    .flatMap((g) => g.songs)
    .reduce((sum, s) => sum + (Number(s.duration) || 0), 0)
  return (seconds / 3600).toFixed(1)
})

const play = (song) => playSong(song.id, allIds.value)
const playAll = () => {
  if (allIds.value.length) playSong(allIds.value[0], allIds.value)
}

const clear = async () => {
  if (!total.value) return
  try {
    await api.clearRecent()
    await refreshRecent()
    toast('已清空播放记录')
  } catch (error) {
    toast(error?.message || '清空失败')
  }
}

onMounted(async () => {
  try {
    await refreshRecent()
  } catch (error) {
    toast(error?.message || '加载最近播放失败')
  }
})
</script>

<template>
  <div class="page">
    <div class="page__canvas recent">
      <PageNav title="最近播放" fallback="/profile">
        <template #right>
          <button type="button" class="clear" :disabled="!total" @click="clear">清空</button>
        </template>
      </PageNav>

      <button type="button" class="summary" :disabled="!total" @click="playAll">
        <span class="summary__icon">
          <Icon name="clock" :size="24" :stroke="1.7" />
        </span>
        <span class="summary__text">
          <span class="summary__title num">共 {{ total }} 首</span>
          <span class="summary__sub num">约 {{ hoursText }} 小时 · 点此全部播放</span>
        </span>
        <span class="summary__play">
          <Icon name="play" :size="15" />
        </span>
      </button>

      <template v-if="total">
        <section v-for="g in groups" :key="g.label" class="group">
          <div class="ghead">
            <p class="glabel">{{ g.label }}</p>
            <span class="gcount num">{{ g.songs.length }} 首</span>
          </div>

          <ul class="list">
            <li v-for="song in g.songs" :key="song.id" class="item">
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
            </li>
          </ul>
        </section>
      </template>

      <div v-else class="empty">
        <span class="empty__icon"><Icon name="clock" :size="26" :stroke="1.6" /></span>
        <p class="empty__title">还没有播放记录</p>
        <p class="empty__sub">听过的歌会自动出现在这里</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recent {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 140px;
}

.clear {
  font-size: 13px;
  line-height: 22px;
  color: var(--ink-sub);
}

.clear:active {
  color: var(--primary);
}

.clear:disabled {
  color: var(--placeholder);
  cursor: default;
}

/* 概览卡 342 × 76 */
.summary {
  width: 100%;
  height: 76px;
  padding: 0 14px 0 16px;
  border-radius: var(--r-card);
  background: var(--sunset-soft);
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
  transition: transform 0.16s ease;
}

.summary:active {
  transform: scale(0.99);
}

.summary:disabled {
  opacity: 0.7;
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
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  box-shadow: var(--shadow-play);
}

/* 分组 */
.group {
  margin-top: 24px;
}

.ghead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 0 2px;
}

.glabel {
  font-size: 13px;
  font-weight: 600;
  line-height: 18px;
  letter-spacing: 0.3px;
  color: var(--ink-sub);
}

.gcount {
  font-size: 12px;
  line-height: 16px;
  color: var(--placeholder);
}

.list {
  margin-top: 10px;
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
  padding: 0 16px 0 14px;
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
}

/* 空状态 */
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
