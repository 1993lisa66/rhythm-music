<script setup>
import Icon from './Icon.vue'
import { fmtTime } from '@/utils/format'

defineProps({
  index: { type: Number, required: true },
  title: { type: String, required: true },
  artist: { type: String, default: '' },
  duration: { type: [Number, String], required: true },
  active: { type: Boolean, default: false },
  /* 自己创建的歌单才允许把歌曲移出 */
  removable: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'remove'])
</script>

<template>
  <!-- 根节点用 div 而非 button：右侧移除按钮不能嵌在 button 里 -->
  <div
    class="track"
    :class="{ 'track--on': active }"
    role="button"
    tabindex="0"
    @click="emit('select')"
    @keydown.enter.prevent="emit('select')"
  >
    <span class="track__no num">{{ String(index).padStart(2, '0') }}</span>
    <span class="track__main">
      <span class="track__title">{{ title }}</span>
      <span v-if="artist" class="track__artist">{{ artist }}</span>
    </span>
    <span class="track__dur num">{{ typeof duration === 'number' ? fmtTime(duration) : duration }}</span>
    <button
      v-if="removable"
      type="button"
      class="track__rm"
      aria-label="从歌单移除"
      @click.stop="emit('remove')"
    >
      <Icon name="trash" :size="15" :stroke="1.7" />
    </button>
  </div>
</template>

<style scoped>
.track {
  width: 100%;
  height: 52px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  text-align: left;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.16s ease;
}

.track__rm {
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  margin-right: -4px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--placeholder);
  transition: background 0.16s ease, color 0.16s ease;
}

.track__rm:hover {
  background: rgba(196, 84, 63, 0.1);
  color: #c4543f;
}

.track:hover {
  background: rgba(245, 239, 227, 0.55);
}

.track__no {
  font-size: 12px;
  color: var(--placeholder);
  width: 20px;
  flex: 0 0 auto;
}

.track__main {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track__title {
  font-size: 15px;
  line-height: 19px;
  font-weight: 500;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.track__artist {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.track__dur {
  font-size: 12px;
  color: var(--ink-sub);
  flex: 0 0 auto;
}

.track--on .track__no,
.track--on .track__title {
  color: var(--primary);
}

.track--on .track__title {
  font-weight: 600;
}
</style>
