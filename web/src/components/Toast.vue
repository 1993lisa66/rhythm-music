<script setup>
import { onMounted, ref } from 'vue'
import { runToastAction, toastState } from '@/store/toast'

/* 等设备外壳挂载到 document 后再 Teleport，避免首屏找不到目标 */
const ready = ref(false)
onMounted(() => {
  ready.value = true
})
</script>

<template>
  <Teleport v-if="ready" to=".device">
    <transition name="tip">
      <div v-if="toastState.visible" class="tip" role="status" aria-live="polite">
        <span class="tip__text">{{ toastState.text }}</span>
        <button
          v-if="toastState.actionLabel"
          type="button"
          class="tip__act"
          @click.stop="runToastAction"
        >
          {{ toastState.actionLabel }}
        </button>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.tip {
  position: absolute;
  left: 50%;
  bottom: 168px;
  z-index: 90;
  transform: translateX(-50%);
  max-width: 320px;
  padding: 10px 14px 10px 18px;
  border-radius: 16px;
  background: rgba(43, 31, 26, 0.92);
  color: #fff3e0;
  font-size: 13px;
  line-height: 18px;
  text-align: center;
  pointer-events: none;
  box-shadow: 0 10px 26px rgba(43, 31, 26, 0.26);
  display: flex;
  align-items: center;
  gap: 10px;
}

.tip__text {
  min-width: 0;
}

/* 撤销按钮：热区 44 高，用主色保证可发现 */
.tip__act {
  flex: 0 0 auto;
  padding: 11px 8px;
  margin: -11px -4px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #ffb08a;
  pointer-events: auto;
}

.tip-enter-active,
.tip-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.tip-enter-from,
.tip-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}
</style>
