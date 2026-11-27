<script setup>
import { onMounted, ref } from 'vue'
import Icon from './Icon.vue'

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  actions: { type: Array, default: () => [] },
  cancelText: { type: String, default: '取消' }
})

const emit = defineEmits(['pick', 'close'])

/* 等设备外壳挂载到 document 后再 Teleport，避免首屏找不到目标 */
const ready = ref(false)
onMounted(() => {
  ready.value = true
})
</script>

<template>
  <Teleport v-if="ready" to=".device">
    <transition name="scrim">
      <div v-if="open" class="scrim" @click.self="emit('close')">
        <div class="sheet" role="dialog" aria-modal="true" :aria-label="title || '更多操作'">
          <span class="sheet__grip" aria-hidden="true"></span>
          <p v-if="title" class="sheet__title">{{ title }}</p>
          <p v-if="subtitle" class="sheet__sub">{{ subtitle }}</p>

          <div class="sheet__list">
            <button
              v-for="a in actions"
              :key="a.key"
              type="button"
              class="srow"
              :class="{ 'srow--danger': a.danger, 'srow--on': a.active }"
              @click="emit('pick', a.key)"
            >
              <Icon v-if="a.icon" :name="a.icon" :size="19" :stroke="1.8" />
              <span class="srow__label">{{ a.label }}</span>
              <Icon v-if="a.active" class="srow__check" name="check" :size="16" :stroke="2.2" />
            </button>
          </div>

          <button type="button" class="sheet__cancel" @click="emit('close')">{{ cancelText }}</button>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.scrim {
  position: absolute;
  inset: 0;
  z-index: 70;
  background: rgba(43, 31, 26, 0.32);
  display: flex;
  align-items: flex-end;
  backdrop-filter: blur(2px);
}

.sheet {
  width: 100%;
  padding: 10px 16px 18px;
  border-radius: 28px 28px 0 0;
  background: #fffdf8;
  box-shadow: 0 -12px 40px rgba(43, 31, 26, 0.2);
}

.sheet__grip {
  display: block;
  width: 40px;
  height: 4px;
  margin: 0 auto 12px;
  border-radius: 2px;
  background: var(--surface-soft);
}

.sheet__title {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--ink);
  text-align: center;
}

.sheet__sub {
  margin-top: 4px;
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-sub);
  text-align: center;
}

.sheet__list {
  margin-top: 12px;
  border-radius: 18px;
  background: var(--surface-soft);
  overflow: hidden;
}

.srow {
  width: 100%;
  height: 52px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  color: var(--ink);
  text-align: left;
  transition: background 0.16s ease;
}

.srow + .srow {
  box-shadow: inset 0 1px 0 rgba(43, 31, 26, 0.06);
}

.srow:active {
  background: rgba(224, 120, 86, 0.1);
}

.srow__label {
  flex: 1 1 auto;
  min-width: 0;
}

.srow--on .srow__label,
.srow--on :deep(.ico) {
  color: var(--primary);
}

.srow__check {
  color: var(--primary);
}

.srow--danger,
.srow--danger :deep(.ico) {
  color: #c4543f;
}

.sheet__cancel {
  width: 100%;
  height: 52px;
  margin-top: 10px;
  border-radius: 18px;
  background: var(--surface-soft);
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-sub);
}

.sheet__cancel:active {
  background: rgba(43, 31, 26, 0.06);
}

.scrim-enter-active,
.scrim-leave-active {
  transition: opacity 0.2s ease;
}

.scrim-enter-from,
.scrim-leave-to {
  opacity: 0;
}

.scrim-enter-active .sheet,
.scrim-leave-active .sheet {
  transition: transform 0.26s cubic-bezier(0.32, 0.72, 0, 1);
}

.scrim-enter-from .sheet,
.scrim-leave-to .sheet {
  transform: translateY(100%);
}
</style>
