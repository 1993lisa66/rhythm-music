<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import { clearQueue, current, playAt, queueSongs, removeAt, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const router = useRouter()

const queueTotal = computed(() => queueSongs.value.length)

/* 「接下来」只列当前曲目之后的歌 —— 正在播放的已经在上面单独成卡，
   同一首歌出现两次会让人分不清点 × 是移出队列还是切歌 */
const upNext = computed(() => {
  const start = Math.max(0, state.index) + 1
  return queueSongs.value.slice(start).map((song, i) => ({ song, index: start + i }))
})
const remainText = computed(() => `${upNext.value.length} 首`)

const jump = (index) => playAt(index)

const remove = (index) => {
  if (!removeAt(index)) toast('队列至少保留一首歌')
}

/* 清空队列是破坏性操作，先在面板里确认，避免误触把后面的歌全丢掉 */
const confirming = ref(false)
const clear = () => {
  if (!queueTotal.value) {
    toast('队列已经空了')
    return
  }
  confirming.value = true
}
const doClear = () => {
  clearQueue()
  confirming.value = false
  toast('已清空队列，仅保留当前播放')
}
const onPick = (key) => {
  if (key === 'clear') doClear()
  else confirming.value = false
}
const clearActions = [
  { key: 'keep', label: '保留队列' },
  { key: 'clear', label: `清空 ${queueTotal.value} 首待播`, danger: true }
]

const openNow = () => router.push('/now')
</script>

<template>
  <div class="page">
    <div class="page__canvas queue">
      <PageNav title="播放队列" fallback="/discover">
        <template #right>
          <button type="button" class="clear hit" @click="clear">清空</button>
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

      <ul v-if="upNext.length" class="list">
        <li v-for="(item, i) in upNext" :key="item.song.id + item.index" class="item">
          <button type="button" class="item__main" @click="jump(item.index)">
            <span class="item__idx num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="item__cover" :style="coverStyle(item.song.cover)"></span>
            <span class="item__text">
              <span class="item__title">{{ item.song.title }}</span>
              <span class="item__sub">{{ item.song.artist }}</span>
            </span>
          </button>
          <button type="button" class="item__del hit" aria-label="从队列移除" @click="remove(item.index)">
            <Icon name="close" :size="14" :stroke="2" />
          </button>
        </li>
      </ul>

      <p v-else class="list__empty">后面没有待播歌曲了，去乐库添几首吧</p>
    </div>

    <ActionSheet
      :open="confirming"
      title="清空播放队列"
      subtitle="只保留当前播放的这首歌，其余待播曲目将移出队列"
      :actions="clearActions"
      @pick="onPick"
      @close="confirming = false"
    />
  </div>
</template>

<style scoped>
.list__empty {
  margin: 8px 4px 0;
  font-size: 13px;
  line-height: 20px;
  color: var(--placeholder);
}

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
