<script setup>
import { useRoute, useRouter } from 'vue-router'
import Icon from './Icon.vue'

const route = useRoute()
const router = useRouter()

const tabs = [
  { key: 'discover', label: '发现', icon: 'home', to: '/discover', pos: 39 },
  { key: 'library', label: '乐库', icon: 'library', to: '/library', pos: 109 },
  { key: 'search', label: '搜索', icon: 'search', to: '/search', pos: 249 },
  { key: 'profile', label: '我的', icon: 'user', to: '/profile', pos: 319 }
]

const isActive = (key) => route.meta.tab === key
const go = (to) => {
  if (route.path !== to) router.push(to)
}
</script>

<template>
  <nav class="tabbar glass" aria-label="主导航">
    <button
      v-for="t in tabs"
      :key="t.key"
      type="button"
      class="tab"
      :class="{ 'tab--on': isActive(t.key) }"
      :style="{ left: `${t.pos}px` }"
      :aria-current="isActive(t.key) ? 'page' : undefined"
      @click="go(t.to)"
    >
      <Icon :name="t.icon" :size="20" :stroke="1.8" />
      <span class="tab__label">{{ t.label }}</span>
    </button>

    <button type="button" class="play" aria-label="打开正在播放" @click="go('/now')">
      <Icon name="play" :size="20" />
    </button>
  </nav>
</template>

<style scoped>
.tabbar {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: var(--nav-b);
  height: var(--nav-h);
  border-radius: var(--r-tab);
  box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.35), var(--shadow-tabbar);
  z-index: 50;
}

.tab {
  position: absolute;
  top: 12px;
  width: 60px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: var(--placeholder);
  transition: color 0.18s ease, transform 0.18s ease;
}

.tab__label {
  font-size: 10px;
  line-height: 12px;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

.tab--on {
  color: var(--primary);
}

.tab--on .tab__label {
  font-weight: 600;
}

.tab:active {
  transform: translateX(-50%) scale(0.92);
}

.play {
  position: absolute;
  left: 179px;
  top: 4px;
  transform: translateX(-50%);
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: var(--shadow-play);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.play :deep(.ico) {
  transform: translateX(1px);
}

.play:active {
  transform: translateX(-50%) scale(0.94);
  box-shadow: 0 2px 8px rgba(224, 120, 86, 0.3);
}
</style>
