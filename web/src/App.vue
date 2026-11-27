<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import StatusBar from './components/StatusBar.vue'
import TabBar from './components/TabBar.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import Toast from './components/Toast.vue'
import { auth } from './store/auth'
import { initAudio } from './store/audio'
import { syncPlayer, tick } from './store/player'
import { loadSettings } from './store/settings'

const route = useRoute()
const immersive = computed(() => !!route.meta.immersive)
const bare = computed(() => !!route.meta.bare)
const subpage = computed(() => !!route.meta.subpage)
const chrome = computed(() => !immersive.value && !bare.value)

let timer = null

const hydrate = async () => {
  if (!auth.user) return
  try {
    await Promise.all([syncPlayer(), loadSettings()])
  } catch {
    /* 播放态加载失败不阻塞页面，页面内操作会再次触发 */
  }
}

onMounted(() => {
  initAudio()
  timer = window.setInterval(tick, 1000)
  hydrate()
})

watch(
  () => auth.user?.id,
  (id) => {
    if (id) hydrate()
  }
)

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div class="app-shell">
    <div class="device" :class="{ 'device--dark': immersive }">
      <StatusBar :light="immersive" />

      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>

      <template v-if="chrome">
        <MiniPlayer :compact="subpage" />
        <TabBar v-if="!subpage" />
      </template>

      <Toast />
    </div>
  </div>
</template>

<style>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
}
</style>
