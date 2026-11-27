<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <button
    type="button"
    role="switch"
    class="sw hit"
    :class="{ 'sw--on': modelValue }"
    :aria-checked="modelValue"
    :aria-label="label"
    @click="emit('update:modelValue', !modelValue)"
  >
    <span class="sw__knob"></span>
  </button>
</template>

<style scoped>
.sw {
  position: relative;
  width: 46px;
  height: 28px;
  border-radius: 14px;
  background: var(--surface-soft);
  flex: 0 0 auto;
  transition: background 0.2s ease;
}

.sw--on {
  background: var(--primary);
}

.sw__knob {
  position: absolute;
  left: 3px;
  top: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(43, 31, 26, 0.18);
  transition: transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}

.sw--on .sw__knob {
  transform: translateX(18px);
}
</style>
