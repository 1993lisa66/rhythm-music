<script setup>
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import playlists from '@/data/playlists.json'
import { coverStyle } from '@/utils/format'

const router = useRouter()

const open = (p) => router.push(`/playlist/${p.id}`)
</script>

<template>
  <div class="page">
    <div class="page__canvas mylists">
      <PageNav title="我的歌单" fallback="/profile">
        <template #right>
          <span class="count num">{{ playlists.length }} 个</span>
        </template>
      </PageNav>

      <ul class="list">
        <li v-for="p in playlists" :key="p.id" class="item">
          <button type="button" class="item__main" @click="open(p)">
            <span class="item__cover" :style="coverStyle(p.cover, 0.32)">
              <span class="item__note">
                <Icon name="note" :size="18" :stroke="1.7" />
              </span>
            </span>
            <span class="item__text">
              <span class="item__title">{{ p.title }}</span>
              <span class="item__sub">{{ p.badge }} · {{ p.count }} 首 · {{ p.durationText }}</span>
            </span>
            <Icon class="item__chevron" name="chevron" :size="14" :stroke="1.8" />
          </button>
        </li>
      </ul>

      <p class="tip">共 {{ playlists.length }} 个歌单，点击进入查看曲目</p>
    </div>
  </div>
</template>

<style scoped>
.mylists {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 140px;
}

.count {
  font-size: 13px;
  line-height: 22px;
  color: var(--ink-sub);
}

.list {
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 6px 0;
  overflow: hidden;
}

.item {
  display: flex;
  align-items: center;
}

.item + .item {
  box-shadow: inset 0 1px 0 rgba(43, 31, 26, 0.045);
}

.item__main {
  flex: 1 1 auto;
  min-width: 0;
  height: 74px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
}

.item__cover {
  position: relative;
  width: 54px;
  height: 54px;
  border-radius: 14px;
  background-color: var(--surface-cover);
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.item__note {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.28);
  color: #fff;
  display: grid;
  place-items: center;
  backdrop-filter: blur(2px);
}

.item__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 19px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item__sub {
  font-size: 11px;
  line-height: 14px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item__chevron {
  color: var(--placeholder);
  flex: 0 0 auto;
}

.tip {
  margin-top: 14px;
  text-align: center;
  font-size: 11px;
  line-height: 15px;
  color: var(--placeholder);
}
</style>
