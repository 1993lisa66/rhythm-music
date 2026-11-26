<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import { clearQueue, current, playAt, queueSongs, removeAt, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const router = useRouter()

const queueTotal = computed(() => queueSongs.value.length)
const remainText = computed(() => `${queueTotal.value} 首`)

const jump = (index) => playAt(index)

const remove = (index) => {
  if (!removeAt(index)) toast('队列至少保留一首歌')
}

const clear = () => {
  clearQueue()
  toast('已清空队列，仅保留当前播放')
}

const openNow = () => router.push('/now')
</script>

<template>
  <div class="page">
    <div class="page__canvas queue">
      <PageNav title="播放队列" fallback="/discover">
        <template #right>
          <button type="button" class="clear" @click="clear">清空</button>
        </template>
      </PageNav>

      <p class="label">正在播放</p>

      <button type="button" class="now" @click="openNow">
        <span class="now__cover" :style="coverStyle(current.cover)"></span>
        <span class="now__text">
          <span class="now__title">{{ current.title }}</span>
          <span class="now__sub">{{ current.artist }} · {{ current.album }}</span>
        </span>
        <span class="now__icon">
          <Icon :name="state.playing ? 'pause' : 'play'" :size="18" />
        </span>
      </button>

      <div class="label-row">
        <p class="label label--inline">接下来</p>
        <span class="count num">{{ remainText }}</span>
      </div>

      <ul class="list">
        <li v-for="(song, index) in queueSongs" :key="song.id + index" class="item">
          <button type="button" class="item__main" @click="jump(index)">
            <span class="item__idx num" :class="{ 'item__idx--on': index === state.index }">
              <Icon v-if="index === state.index" name="note" :size="14" :stroke="1.8" />
              <template v-else>{{ index + 1 }}</template>
            </span>
            <span class="item__cover" :style="coverStyle(song.cover)"></span>
            <span class="item__text">
              <span class="item__title" :class="{ 'item__title--on': index === state.index }">
                {{ song.title }}
              </span>
              <span class="item__sub">{{ song.artist }}</span>
            </span>
          </button>
          <button type="button" class="item__del" aria-label="从队列移除" @click="remove(index)">
            <Icon name="close" :size="14" :stroke="2" />
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.queue {
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

.label {
  font-size: 13px;
  font-weight: 600;
  line-height: 18px;
  letter-spacing: 0.3px;
  color: var(--ink-sub);
}

.label-row {
  margin-top: 26px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.label--inline {
  margin: 0;
}

.count {
  font-size: 12px;
  color: var(--ink-sub);
}

/* 当前播放 342 × 76 */
.now {
  margin-top: 12px;
  width: 100%;
  height: 76px;
  padding: 0 14px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
  transition: transform 0.16s ease;
}

.now:active {
  transform: scale(0.99);
}

.now__cover {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background-color: var(--surface-cover);
  flex: 0 0 auto;
}

.now__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.now__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 19px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.now__sub {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.now__icon {
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

/* 队列列表 */
.list {
  margin-top: 12px;
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
  height: 60px;
  padding: 0 6px 0 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.item__idx {
  width: 18px;
  font-size: 12px;
  color: var(--placeholder);
  flex: 0 0 auto;
  display: grid;
  place-items: center;
}

.item__idx--on {
  color: var(--primary);
}

.item__cover {
  width: 44px;
  height: 44px;
  border-radius: 11px;
  background-color: var(--surface-cover);
  flex: 0 0 auto;
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
  width: 44px;
  height: 60px;
  display: grid;
  place-items: center;
  color: var(--placeholder);
  flex: 0 0 auto;
  transition: color 0.16s ease;
}

.item__del:hover {
  color: #c4543f;
}
</style>
