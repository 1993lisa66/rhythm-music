<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import { api } from '@/api/client'
import { setLyrics } from '@/store/data'
import { goBack } from '@/utils/nav'
import {
  current,
  currentLyrics,
  lyricIndex,
  next,
  prev,
  seek,
  state,
  toggle
} from '@/store/player'

const router = useRouter()
const lineRefs = ref([])
const searching = ref(false)
const searchTip = ref('')

const lines = computed(() => currentLyrics.value)
const back = () => goBack(router, '/now')

const onlineFetch = async () => {
  const id = current.value?.id
  if (!id || searching.value) return
  searching.value = true
  searchTip.value = ''
  try {
    const payload = await api.fetchLyrics(id)
    setLyrics(id, payload.lines || [])
  } catch (error) {
    searchTip.value = error?.message || '在线曲库暂未收录'
  } finally {
    searching.value = false
  }
}

const setRef = (el, i) => {
  lineRefs.value[i] = el
}

/* 歌词跟随播放进度滚动到视觉中间 */
watch(lyricIndex, async (i) => {
  await nextTick()
  const el = lineRefs.value[i]
  if (el && typeof el.scrollIntoView === 'function') {
    el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
})

/* 歌词开头的「作词：」「编曲：」以及「歌手 - 曲名」这类制作信息，
   不该当成歌词逐行点亮（看起来像识别错了），单独降级显示 */
const CREDIT_RE = /^\s*[\u4e00-\u9fa5A-Za-z0-9（）()·]{1,8}\s*[:：]/
const isCredit = (text) => {
  if (!text) return false
  const title = current.value?.title
  if (title && text.includes(' - ') && text.trim().endsWith(title)) return true
  return CREDIT_RE.test(text)
}
const isHighlight = (i) => i === lyricIndex.value && !isCredit(lines.value[i]?.text)

const pick = (line) => {
  const dur = current.value.duration || 1
  seek(line.t / dur)
}
</script>

<template>
  <div class="page page--dark">
    <div class="page__canvas lyrics">
      <div class="head">
        <button type="button" class="head__btn hit" aria-label="返回" @click="back">
          <Icon name="back" :size="22" :stroke="2" />
        </button>
        <div class="head__text">
          <p class="head__title">{{ current.title }}</p>
          <p class="head__sub">{{ current.artist }}</p>
        </div>
        <span class="head__btn hit" aria-hidden="true"></span>
      </div>

      <div v-if="lines.length" class="lines">
        <button
          v-for="(line, i) in lines"
          :key="i"
          :ref="(el) => setRef(el, i)"
          type="button"
          class="line"
          :class="{
            'line--credit': isCredit(line.text),
            'line--on': isHighlight(i),
            'line--near': !isCredit(line.text) && Math.abs(i - lyricIndex) === 1
          }"
          @click="pick(line)"
        >
          {{ line.text }}
        </button>
      </div>

      <div v-else class="empty">
        <p>这首歌暂时没有歌词</p>
        <button type="button" class="empty__btn" :disabled="searching" @click="onlineFetch">
          {{ searching ? '正在查找…' : '在线查找歌词' }}
        </button>
        <p v-if="searchTip" class="empty__tip">{{ searchTip }}</p>
      </div>

      <div class="bar">
        <button type="button" class="bar__ctrl hit" aria-label="上一首" @click="prev">
          <Icon name="prev" :size="22" />
        </button>
        <button
          type="button"
          class="bar__play"
          :aria-label="state.playing ? '暂停' : '播放'"
          @click="toggle"
        >
          <Icon :name="state.playing ? 'pause' : 'play'" :size="22" />
        </button>
        <button type="button" class="bar__ctrl hit" aria-label="下一首" @click="next(false)">
          <Icon name="next" :size="22" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lyrics {
  height: 800px;
}

.head {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 34px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.head__btn {
  width: 30px;
  height: 30px;
  margin: 0 -4px;
  display: grid;
  place-items: center;
  color: var(--on-dark);
  opacity: 0.8;
}

.head__btn:active {
  opacity: 1;
}

.head__text {
  flex: 1 1 auto;
  min-width: 0;
  text-align: center;
}

.head__title {
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--on-dark);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.head__sub {
  margin-top: 2px;
  font-size: 11px;
  line-height: 14px;
  color: var(--on-dark-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.lines {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 96px;
  bottom: 128px;
  overflow-y: auto;
  scrollbar-width: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 22px;
  padding: 60px 0;
  -webkit-mask-image: linear-gradient(180deg, transparent 0, #000 56px, #000 calc(100% - 56px), transparent 100%);
  mask-image: linear-gradient(180deg, transparent 0, #000 56px, #000 calc(100% - 56px), transparent 100%);
}

.lines::-webkit-scrollbar {
  width: 0;
}

.line {
  max-width: 100%;
  font-size: 16px;
  line-height: 24px;
  text-align: center;
  color: rgba(255, 243, 224, 0.34);
  transition: color 0.24s ease, transform 0.24s ease;
}

/* 制作信息：小一号、更淡，不参与高亮 */
.line--credit {
  font-size: 12.5px;
  line-height: 20px;
  color: rgba(255, 243, 224, 0.24);
  letter-spacing: 0.2px;
}

.line--near {
  color: rgba(255, 243, 224, 0.62);
}

.line--on {
  color: var(--on-dark);
  font-size: 19px;
  font-weight: 700;
  line-height: 28px;
  transform: scale(1.02);
  text-shadow: 0 6px 22px rgba(255, 126, 84, 0.45);
}

.empty {
  padding-top: 160px;
  text-align: center;
  font-size: 14px;
  color: var(--on-dark-sub);
}

.empty__btn {
  margin-top: 18px;
  height: 36px;
  padding: 0 18px;
  border-radius: 18px;
  background: var(--primary);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.empty__btn:disabled {
  opacity: 0.6;
}

.empty__tip {
  margin-top: 12px;
  font-size: 12px;
  color: var(--on-dark-sub);
  opacity: 0.8;
}

.bar {
  position: absolute;
  left: 50%;
  bottom: 46px;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 28px;
}

.bar__ctrl {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--on-dark);
  background: rgba(255, 243, 224, 0.1);
}

.bar__play {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #2b1f1a;
  background: var(--on-dark);
  box-shadow: 0 10px 26px rgba(255, 126, 84, 0.35);
}

.bar__play:active,
.bar__ctrl:active {
  transform: scale(0.94);
}
</style>
