<script setup>
import { coverStyle, fmtTime } from '@/utils/format'

const props = defineProps({
  song: { type: Object, required: true },
  duration: { type: [Number, String], default: null },
  active: { type: Boolean, default: false }
})

defineEmits(['select'])
</script>

<template>
  <button type="button" class="row" :class="{ 'row--on': active }" @click="$emit('select', song)">
    <span class="row__cover" :style="coverStyle(song.cover)">
      <span v-if="active" class="row__wave" aria-hidden="true">
        <i></i><i></i><i></i>
      </span>
    </span>
    <span class="row__body">
      <span class="row__title">{{ song.title }}</span>
      <span class="row__sub">{{ song.artist }}</span>
    </span>
    <span class="row__dur num">{{ duration ?? fmtTime(song.duration) }}</span>
  </button>
</template>

<style scoped>
.row {
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 16px;
  border-radius: 14px;
  text-align: left;
  transition: background 0.16s ease;
}

.row:hover {
  background: rgba(245, 239, 227, 0.6);
}

.row:active {
  background: var(--surface-soft);
}

.row__cover {
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  flex: 0 0 auto;
  background-color: var(--surface-cover);
  overflow: hidden;
}

.row__body {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.row__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.row__sub {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.row__dur {
  font-size: 12px;
  color: var(--ink-sub);
  flex: 0 0 auto;
  margin-left: 8px;
}

.row--on .row__title {
  color: var(--primary);
}

/* 正在播放的三根跳动的柱子 */
.row__wave {
  position: absolute;
  inset: 0;
  background: rgba(43, 31, 26, 0.34);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.row__wave i {
  width: 2.5px;
  border-radius: 2px;
  background: #fff;
  animation: wave 0.9s ease-in-out infinite;
}

.row__wave i:nth-child(1) {
  height: 8px;
  animation-delay: -0.2s;
}
.row__wave i:nth-child(2) {
  height: 13px;
}
.row__wave i:nth-child(3) {
  height: 6px;
  animation-delay: -0.4s;
}

@keyframes wave {
  0%,
  100% {
    transform: scaleY(0.55);
  }
  50% {
    transform: scaleY(1);
  }
}
</style>
