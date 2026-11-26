<script setup>
import { fmtTime } from '@/utils/format'

defineProps({
  index: { type: Number, required: true },
  title: { type: String, required: true },
  artist: { type: String, default: '' },
  duration: { type: [Number, String], required: true },
  active: { type: Boolean, default: false }
})

defineEmits(['select'])
</script>

<template>
  <button type="button" class="track" :class="{ 'track--on': active }" @click="$emit('select')">
    <span class="track__no num">{{ String(index).padStart(2, '0') }}</span>
    <span class="track__main">
      <span class="track__title">{{ title }}</span>
      <span v-if="artist" class="track__artist">{{ artist }}</span>
    </span>
    <span class="track__dur num">{{ typeof duration === 'number' ? fmtTime(duration) : duration }}</span>
  </button>
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
  transition: background 0.16s ease;
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
