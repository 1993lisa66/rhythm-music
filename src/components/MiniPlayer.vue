<script setup>
import { useRouter } from 'vue-router'
import Icon from './Icon.vue'
import { current, state, toggle } from '@/store/player'
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

    <button type="button" class="mini__play" :aria-label="state.playing ? '暂停' : '播放'"
      @click.stop="toggle">
      <Icon :name="state.playing ? 'pause' : 'play'" :size="compact ? 13 : 14" />
    </button>
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
  bottom: 16px;
  padding-left: 20px;
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

.mini__play {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  margin-left: auto;
  margin-right: 6px;
  transition: transform 0.16s ease, background 0.16s ease;
}

.mini--compact .mini__play {
  margin-right: 20px;
}

.mini__play :deep(.ico) {
  transform: translateX(1px);
}

.mini__play:active {
  transform: scale(0.92);
}
</style>
