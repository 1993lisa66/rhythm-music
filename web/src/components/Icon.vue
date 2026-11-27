<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  stroke: { type: [Number, String], default: 1.8 },
  filled: { type: Boolean, default: false }
})

/* 线性图标：1.8px 描边，禁止 emoji / 字体图标 */
const LINEAR = {
  home: '<path d="M3.6 10.4 12 3.4l8.4 7v9.1a1.6 1.6 0 0 1-1.6 1.6h-4.3v-6.2H9.5v6.2H5.2a1.6 1.6 0 0 1-1.6-1.6z"/>',
  library:
    '<rect x="3.6" y="4.2" width="5.4" height="15.6" rx="1.4"/><rect x="11" y="4.2" width="5.4" height="15.6" rx="1.4"/><path d="M18.6 5.4 21 19.2"/>',
  search: '<circle cx="11" cy="11" r="6.4"/><path d="m16 16 4.2 4.2"/>',
  user: '<circle cx="12" cy="8.4" r="3.9"/><path d="M4.8 20.4a7.2 7.2 0 0 1 14.4 0"/>',
  back: '<path d="M14.6 5.4 8 12l6.6 6.6"/>',
  settings:
    '<circle cx="12" cy="12" r="3.1"/><path d="M19.1 14.5a1.5 1.5 0 0 0 .3 1.65l.06.06a1.9 1.9 0 1 1-2.7 2.7l-.05-.06a1.5 1.5 0 0 0-1.65-.3 1.5 1.5 0 0 0-.9 1.37V20a1.9 1.9 0 0 1-3.8 0v-.11a1.5 1.5 0 0 0-.98-1.37 1.5 1.5 0 0 0-1.65.3l-.06.06a1.9 1.9 0 1 1-2.7-2.7l.06-.05a1.5 1.5 0 0 0 .3-1.65 1.5 1.5 0 0 0-1.37-.9H4a1.9 1.9 0 0 1 0-3.8h.11a1.5 1.5 0 0 0 1.37-.98 1.5 1.5 0 0 0-.3-1.65l-.06-.06a1.9 1.9 0 1 1 2.7-2.7l.05.06a1.5 1.5 0 0 0 1.65.3H9.6a1.5 1.5 0 0 0 .9-1.37V4a1.9 1.9 0 0 1 3.8 0v.11a1.5 1.5 0 0 0 .9 1.37 1.5 1.5 0 0 0 1.65-.3l.06-.06a1.9 1.9 0 1 1 2.7 2.7l-.06.05a1.5 1.5 0 0 0-.3 1.65v.08a1.5 1.5 0 0 0 1.37.9H20a1.9 1.9 0 0 1 0 3.8h-.11a1.5 1.5 0 0 0-1.37.9z"/>',
  filter:
    '<path d="M4 7.6h8.4M15.8 7.6H20M4 16.4h3.4M11 16.4h9"/><circle cx="14.2" cy="7.6" r="2"/><circle cx="9.2" cy="16.4" r="2"/>',
  heart:
    '<path d="M12 20.3 4.5 12.9a4.95 4.95 0 0 1 7-7l.5.5.5-.5a4.95 4.95 0 0 1 7 7z"/>',
  shuffle:
    '<path d="M3 6.6h3.2l9.4 10.8h3.6M3 17.4h3.2l2.2-2.6"/><path d="M14.4 9 17 6.6"/><path d="M16.6 3.6h4v4M16.6 20.4h4v-4"/>',
  repeat:
    '<path d="M6.6 3.6 3.4 6.8l3.2 3.2"/><path d="M3.6 6.8h11.2a4.6 4.6 0 0 1 4.6 4.6v1"/><path d="M17.4 20.4l3.2-3.2-3.2-3.2"/><path d="M20.4 17.2H9.2a4.6 4.6 0 0 1-4.6-4.6v-1"/>',
  queue:
    '<path d="M3.6 6.4h9.6M3.6 11.6h9.6M3.6 16.8h6"/><path d="M19.4 5v9.8"/><circle cx="17.4" cy="16.6" r="2.2"/>',
  download: '<path d="M12 3.8v10.4M7.8 10.4 12 14.6l4.2-4.2M4.6 20.2h14.8"/>',
  clock: '<circle cx="12" cy="12" r="8.2"/><path d="M12 7.2V12l3.3 2"/>',
  chevron: '<path d="m9.6 5.6 6.4 6.4-6.4 6.4"/>',
  playlist: '<path d="M4 6.2h9.4M4 11.4h9.4M4 16.6h5.2"/><circle cx="16.6" cy="15.6" r="2.6"/><path d="M19.2 15.6V6l2.2-.5"/>',
  refresh: '<path d="M20 11.4A8.2 8.2 0 1 0 17.6 17"/><path d="M20 4.8v6.6h-6.6"/>',
  note: '<path d="M9.4 18V5.6l9.2-1.9v12.5"/><ellipse cx="6.9" cy="18" rx="2.5" ry="2.3"/><ellipse cx="16.1" cy="16.2" rx="2.5" ry="2.3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  mic: '<rect x="9" y="3.4" width="6" height="10.4" rx="3"/><path d="M5.6 11.4a6.4 6.4 0 0 0 12.8 0M12 17.8V20.6"/>',
  quote:
    '<path d="M4.6 5.8h14.8v10.2H10l-3.6 2.8v-2.8H4.6z"/><path d="M9.2 9.8h5.6M9.2 12.6h3.6"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  check: '<path d="m5 12.6 4.6 4.6L19 6.6"/>',
  trash:
    '<path d="M4.6 6.8h14.8"/><path d="M9.4 6.8V4.6h5.2v2.2"/><path d="M6.6 6.8 7.4 19a1.6 1.6 0 0 0 1.6 1.5h6a1.6 1.6 0 0 0 1.6-1.5l.8-12.2"/><path d="M10.4 10.6v6M13.6 10.6v6"/>',
  share:
    '<circle cx="17.6" cy="6" r="2.6"/><circle cx="6.4" cy="12" r="2.6"/><circle cx="17.6" cy="18" r="2.6"/><path d="m8.8 10.8 6.4-3.6M8.8 13.2l6.4 3.6"/>',
  moon: '<path d="M20 14.6A8.4 8.4 0 1 1 9.4 4a6.8 6.8 0 0 0 10.6 10.6z"/>',
  bell:
    '<path d="M18 15.4V11a6 6 0 1 0-12 0v4.4L4.6 18h14.8z"/><path d="M9.8 20.4a2.4 2.4 0 0 0 4.4 0"/>',
  wifi:
    '<path d="M2.8 8.6a13 13 0 0 1 18.4 0"/><path d="M6.2 12a8.2 8.2 0 0 1 11.6 0"/><path d="M9.6 15.4a3.6 3.6 0 0 1 4.8 0"/><circle cx="12" cy="18.8" r="0.9"/>',
  info:
    '<circle cx="12" cy="12" r="8.4"/><path d="M12 11v5.4"/><circle cx="12" cy="7.8" r="0.9"/>',
  timer:
    '<circle cx="12" cy="13.4" r="7.4"/><path d="M12 9.6v3.8l2.4 1.6M9.4 3.4h5.2"/>',
  logout:
    '<path d="M14.6 4.6H18a1.6 1.6 0 0 1 1.6 1.6v11.6A1.6 1.6 0 0 1 18 19.4h-3.4"/><path d="m10 8.2-3.8 3.8L10 15.8"/><path d="M6.2 12h9.2"/>',
  folder:
    '<path d="M3.8 7.2a1.6 1.6 0 0 1 1.6-1.6h3.4l2 2.4h7.8a1.6 1.6 0 0 1 1.6 1.6v8.2a1.6 1.6 0 0 1-1.6 1.6H5.4a1.6 1.6 0 0 1-1.6-1.6z"/>',
  mail: '<rect x="3.4" y="5.6" width="17.2" height="12.8" rx="2.4"/><path d="m4.6 8 6.8 4.9a1.2 1.2 0 0 0 1.2 0L19.4 8"/>',
  lock: '<rect x="4.8" y="10.4" width="14.4" height="9.2" rx="2.4"/><path d="M8.4 10.4V8a3.6 3.6 0 0 1 7.2 0v2.4"/>',
  eye: '<path d="M2.6 12S6 6.6 12 6.6 21.4 12 21.4 12 18 17.4 12 17.4 2.6 12 2.6 12z"/><circle cx="12" cy="12" r="2.9"/>',
  eyeOff:
    '<path d="M4.4 8.2C3.2 9.4 2.6 12 2.6 12s3.4 5.4 9.4 5.4c1.7 0 3.2-.4 4.5-1.1"/><path d="M9.5 6.9c.8-.2 1.6-.3 2.5-.3 6 0 9.4 5.4 9.4 5.4s-1 1.6-2.8 3"/><path d="M10.2 10.2a2.9 2.9 0 0 0 3.9 4"/><path d="m4 4 16 16"/>'
}

/* 实心图标（播放三角、暂停、圆点等） */
const SOLID = {
  play: '<path d="M8.6 5.5c0-.72.79-1.16 1.4-.79l8.66 6.49a.94.94 0 0 1 0 1.57L10 19.27c-.61.37-1.4-.07-1.4-.79z"/>',
  pause:
    '<rect x="7.2" y="4.8" width="3.6" height="14.4" rx="1.4"/><rect x="13.2" y="4.8" width="3.6" height="14.4" rx="1.4"/>',
  more: '<circle cx="5.4" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18.6" cy="12" r="1.6"/>',
  prev: '<path d="M18.4 5.6c0-.5-.55-.8-.97-.53L8.9 11.3a.64.64 0 0 0 0 1.06l8.53 5.83c.42.27.97-.03.97-.53z"/><rect x="4.8" y="5.2" width="2" height="13.6" rx="1"/>',
  next: '<path d="M5.6 5.6c0-.5.55-.8.97-.53l8.53 5.83a.64.64 0 0 1 0 1.06l-8.53 5.83c-.42.27-.97-.03-.97-.53z"/><rect x="17.2" y="5.2" width="2" height="13.6" rx="1"/>'
}

const svg = computed(() => {
  const solid = SOLID[props.name]
  const body = solid || LINEAR[props.name] || ''
  const paint =
    solid || props.filled
      ? 'fill="currentColor" stroke="none"'
      : `fill="none" stroke="currentColor" stroke-width="${props.stroke}"`
  return `<svg viewBox="0 0 24 24" width="100%" height="100%" ${paint} stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${body}</svg>`
})
</script>

<template>
  <span class="ico" :style="{ width: `${size}px`, height: `${size}px` }" v-html="svg" />
</template>

<style scoped>
.ico {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
}
.ico :deep(svg) {
  display: block;
  overflow: visible;
}
</style>
