<script setup>
defineProps({
  title: { type: String, required: true },
  more: { type: String, default: '' }
})

defineEmits(['more'])
</script>

<template>
  <div class="sh">
    <h2 class="sh__title">{{ title }}</h2>
    <button v-if="more" type="button" class="sh__more" @click="$emit('more')">{{ more }}</button>
  </div>
</template>

<style scoped>
.sh {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 24px;
}

.sh__title {
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
  letter-spacing: 0.2px;
  color: var(--ink);
}

.sh__more {
  font-size: 13px;
  line-height: 18px;
  color: var(--primary);
  padding: 4px 0 4px 10px;
}
</style>
