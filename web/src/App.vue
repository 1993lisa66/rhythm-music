<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
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
/* 只有播放页/歌词（immersive）和登录页（bare）才隐藏整套悬浮层。
   列表型二级页保留 Tab 栏 —— Tab 是全局导航，不该随层级消失。 */
const chrome = computed(() => !immersive.value && !bare.value)

let timer = null
let gapToken = 0

const hydrate = async () => {
  if (!auth.user) return
  try {
    await Promise.all([syncPlayer(), loadSettings()])
  } catch {
    /* 播放态加载失败不阻塞页面，页面内操作会再次触发 */
  }
}

/* 画布本身没超屏时去掉底部兜底留白，避免短页面能拖出一段空白。
   路由切换有过渡，元素会被替换，所以等新节点稳定后再量。 */
const fitBottomGap = () => {
  const token = ++gapToken
  const leaving = document.querySelector('.page')
  let tries = 0
  const tick = () => {
    if (token !== gapToken) return
    const page = document.querySelector('.page')
    if (!page) {
      if (tries++ < 45) requestAnimationFrame(tick)
      return
    }
    if (page === leaving && tries++ < 30) {
      requestAnimationFrame(tick)
      return
    }
    const canvas = page.querySelector('.page__canvas')
    if (!canvas) return
    page.classList.toggle('page--flush', canvas.offsetHeight <= page.clientHeight)
  }
  requestAnimationFrame(tick)
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

watch(
  () => route.fullPath,
  () => {
    fitBottomGap()
    window.setTimeout(fitBottomGap, 400)
    window.setTimeout(fitBottomGap, 1100)
  },
  { immediate: true }
)
</script>

<template>
  <div class="app-shell">
    <div class="device" :class="{ 'device--dark': immersive }">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>

      <template v-if="chrome">
        <MiniPlayer />
        <TabBar />
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
