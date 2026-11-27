<script setup>
import { useRouter } from 'vue-router'
import Icon from './Icon.vue'
import { goBack } from '@/utils/nav'

const props = defineProps({
  title: { type: String, required: true },
  fallback: { type: String, default: '/discover' }
})

const router = useRouter()
const back = () => goBack(router, props.fallback)
</script>

<template>
  <div class="pnav">
    <button type="button" class="pnav__back hit" aria-label="返回" @click="back">
      <Icon name="back" :size="22" :stroke="2" />
    </button>
    <h1 class="pnav__title">{{ title }}</h1>
    <div class="pnav__right">
      <slot name="right" />
    </div>
  </div>
</template>

<style scoped>
.pnav {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 34px;
  height: 22px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.pnav__back {
  width: 22px;
  height: 22px;
  color: var(--ink);
  display: grid;
  place-items: center;
  margin-left: -2px;
  transition: color 0.16s ease;
}

.pnav__back:hover {
  color: var(--primary);
}

.pnav__title {
  font-size: 17px;
  font-weight: 700;
  line-height: 22px;
  color: var(--ink);
  white-space: nowrap;
}

.pnav__right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: var(--primary);
}
</style>
