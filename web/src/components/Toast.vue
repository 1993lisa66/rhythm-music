<script setup>
import { onMounted, ref } from 'vue'
import { toastState } from '@/store/toast'

/* 等设备外壳挂载到 document 后再 Teleport，避免首屏找不到目标 */
const ready = ref(false)
onMounted(() => {
  ready.value = true
})
</script>

<template>
  <Teleport v-if="ready" to=".device">
    <transition name="tip">
      <p v-if="toastState.visible" class="tip" role="status" aria-live="polite">
        {{ toastState.text }}
      </p>
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
  max-width: 300px;
  padding: 10px 18px;
  border-radius: 16px;
  background: rgba(43, 31, 26, 0.9);
  color: #fff3e0;
  font-size: 13px;
  line-height: 18px;
  text-align: center;
  pointer-events: none;
  box-shadow: 0 10px 26px rgba(43, 31, 26, 0.26);
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
