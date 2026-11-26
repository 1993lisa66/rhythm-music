<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import StatusBar from './components/StatusBar.vue'
import TabBar from './components/TabBar.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import Toast from './components/Toast.vue'
import { tick } from './store/player'

const route = useRoute()
const immersive = computed(() => !!route.meta.immersive)
const subpage = computed(() => !!route.meta.subpage)

let timer = null
onMounted(() => {
  timer = window.setInterval(tick, 1000)
})
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

      <template v-if="!immersive">
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
