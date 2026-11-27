<script setup>
import { useRouter } from 'vue-router'
import Icon from './Icon.vue'
import { current, next, progress } from '@/store/player'
import { coverStyle } from '@/utils/format'

defineProps({
  compact: { type: Boolean, default: false }
})

const router = useRouter()
const open = () => router.push('/now')
</script>

<template>
  <div class="mini glass" :class="{ 'mini--compact': compact }" role="button" tabindex="0"
    :aria-label="`正在播放 ${current.title}，点击展开播放页`" @click="open" @keydown.enter="open">
    <div class="mini__cover" :style="coverStyle(current.cover)"></div>

    <div class="mini__text">
      <p class="mini__title">{{ current.title }}</p>
      <p class="mini__artist">{{ current.artist }} · {{ current.album }}</p>
    </div>

    <!-- 播放/暂停交给底部 TabBar 中央键，这里只保留切歌，避免两个圆形按钮同屏 -->
    <button type="button" class="mini__next hit" aria-label="下一首" @click.stop="next(false)">
      <Icon name="next" :size="14" />
    </button>

    <span class="mini__bar" aria-hidden="true">
      <i :style="{ width: `${Math.round(progress * 100)}%` }"></i>
    </span>
  </div>
</template>

<style scoped>
.mini {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: var(--mini-b);
  height: var(--mini-h);
  border-radius: var(--r-mini);
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.3), var(--shadow-mini);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 6px 0 10px;
  z-index: 45;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.18s ease;
}

.mini:active {
  transform: scale(0.985);
}

.mini--compact {
  bottom: calc(16px + var(--sab, 0px));
  padding-left: 20px;
}

/* 毛玻璃太透会让列表文字透到标题上，看起来像渲染重叠 */
.mini {
  background: rgba(255, 250, 242, 0.86);
}

.mini__cover {
  width: 42px;
  height: 42px;
  border-radius: var(--r-thumb);
  background-color: var(--surface-cover);
  flex: 0 0 auto;
}

.mini--compact .mini__cover {
  width: 38px;
  height: 38px;
  border-radius: 10px;
}

.mini__text {
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mini__title {
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.mini--compact .mini__title {
  font-size: 13px;
  line-height: 17px;
}

.mini__artist {
  font-size: 11px;
  line-height: 14px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.mini__next {
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: var(--ink);
  display: grid;
  place-items: center;
  margin-left: auto;
  margin-right: 6px;
  transition: transform 0.16s ease, color 0.16s ease;
}

.mini--compact .mini__next {
  margin-right: 20px;
}

.mini__next:active {
  transform: scale(0.92);
  color: var(--primary);
}

/* 迷你播放器底部的细进度条 */
.mini__bar {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 5px;
  height: 2px;
  border-radius: 2px;
  background: rgba(43, 31, 26, 0.1);
  overflow: hidden;
}

.mini__bar i {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: var(--primary);
  transition: width 0.3s linear;
}
</style>
