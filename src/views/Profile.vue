<script setup>
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import profile from '@/data/profile.json'

const router = useRouter()

const goMenu = (item) => {
  const routes = {
    我的收藏: '/playlist/private',
    最近播放: '/recent',
    离线下载: '/downloads',
    我的歌单: '/mylists'
  }
  const to = routes[item.name]
  if (to) router.push(to)
}

const openSettings = () => router.push('/settings')
</script>

<template>
  <div class="page">
    <div class="page__canvas">
      <h1 class="title">{{ profile.title }}</h1>

      <button type="button" class="settings" aria-label="设置" @click="openSettings">
        <Icon name="settings" :size="22" :stroke="1.7" />
      </button>

      <div class="user">
        <div class="user__avatar">
          <Icon name="user" :size="34" :stroke="1.7" />
        </div>
        <div class="user__info">
          <p class="user__name">{{ profile.user.name }}</p>
          <p class="user__id num">{{ profile.user.id }}</p>
          <span class="user__badge">{{ profile.user.member }}</span>
        </div>
      </div>

      <div class="stats">
        <div v-for="s in profile.stats" :key="s.label" class="stat">
          <span class="stat__value num">{{ s.value }}</span>
          <span class="stat__label">{{ s.label }}</span>
        </div>
      </div>

      <h2 class="menu-title">{{ profile.menu.title }}</h2>

      <div class="menu">
        <button
          v-for="item in profile.menu.items"
          :key="item.name"
          type="button"
          class="mrow"
          @click="goMenu(item)"
        >
          <span class="mrow__icon">
            <Icon :name="item.icon" :size="20" :stroke="1.8" />
          </span>
          <span class="mrow__name">{{ item.name }}</span>
          <span class="mrow__value">{{ item.value }}</span>
          <Icon class="mrow__chevron" name="chevron" :size="14" :stroke="1.8" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.title {
  position: absolute;
  left: 24px;
  top: 30px;
  font-size: 28px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.4px;
  color: var(--ink);
}

.settings {
  position: absolute;
  right: 24px;
  top: 36px;
  width: 22px;
  height: 22px;
  color: var(--ink);
  display: grid;
  place-items: center;
  transition: transform 0.2s ease, color 0.2s ease;
}

.settings:hover {
  color: var(--primary);
  transform: rotate(24deg);
}

/* 用户信息 */
.user {
  position: absolute;
  left: 24px;
  top: 84px;
  display: flex;
  gap: 18px;
}

.user__avatar {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  background-color: var(--primary);
  background-size: cover;
  background-position: center;
  color: #fff;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  box-shadow: 0 6px 18px rgba(224, 120, 86, 0.28);
  position: relative;
  overflow: hidden;
}

.user__avatar :deep(.ico) {
  position: relative;
  z-index: 1;
}

.user__info {
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.user__name {
  font-size: 20px;
  font-weight: 700;
  line-height: 26px;
  color: var(--ink);
}

.user__id {
  font-size: 12px;
  line-height: 15px;
  color: var(--ink-sub);
  letter-spacing: 0.2px;
}

.user__badge {
  margin-top: 2px;
  height: 24px;
  padding: 0 12px;
  border-radius: var(--r-badge);
  background: var(--honey);
  color: #fff;
  font-size: 10px;
  line-height: 24px;
  letter-spacing: 0.4px;
  white-space: nowrap;
}

/* 统计卡片 342 × 76 r20 */
.stats {
  position: absolute;
  left: 24px;
  top: 184px;
  width: 342px;
  height: 76px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  padding: 0 6px;
}

.stat {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.stat__value {
  font-size: 20px;
  font-weight: 700;
  line-height: 24px;
  color: var(--ink);
}

.stat__label {
  font-size: 11px;
  line-height: 14px;
  color: var(--ink-sub);
  white-space: nowrap;
}

.menu-title {
  position: absolute;
  left: 24px;
  top: 288px;
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
  color: var(--ink);
}

/* 功能菜单 342 × 224 r20 */
.menu {
  position: absolute;
  left: 24px;
  top: 324px;
  width: 342px;
  height: 224px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 8px 0;
}

.mrow {
  width: 100%;
  height: 50px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  text-align: left;
  border-radius: 14px;
  transition: background 0.16s ease;
}

.mrow:hover {
  background: rgba(245, 239, 227, 0.66);
}

.mrow__icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--surface-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}

.mrow__name {
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  white-space: nowrap;
}

/* 数值右对齐且不压缩，杜绝「今天 32 首」截断 */
.mrow__value {
  margin-left: auto;
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-sub);
  white-space: nowrap;
  flex: 0 0 auto;
}

.mrow__chevron {
  color: var(--placeholder);
  flex: 0 0 auto;
}
</style>
