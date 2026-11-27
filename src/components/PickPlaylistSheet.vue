<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import Icon from './Icon.vue'
import { api } from '@/api/client'
import { data, refreshPlaylists } from '@/store/data'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  songId: { type: String, default: '' },
  songTitle: { type: String, default: '' }
})
const emit = defineEmits(['close', 'added'])

const ready = ref(false)
const adding = ref('')

onMounted(() => {
  ready.value = true
})

/* 打开时拉取最新歌单，并查询每个歌单是否已有这首歌 */
watch(
  () => props.open,
  async (open) => {
    if (!open) return
    adding.value = ''
    try {
      await refreshPlaylists()
      await loadContains()
    } catch {
      toast('歌单加载失败')
    }
  }
)

const contains = ref({})
const playlists = computed(() => data.playlists || [])

const loadContains = async () => {
  if (!props.songId) return
  const entries = await Promise.all(
    playlists.value.map(async (playlist) => {
      try {
        const detail = await api.playlist(playlist.id)
        return [playlist.id, (detail.tracks || []).some((track) => track.id === props.songId)]
      } catch {
        return [playlist.id, false]
      }
    })
  )
  contains.value = Object.fromEntries(entries)
}

const addTo = async (playlist) => {
  if (!props.songId || adding.value) return
  adding.value = playlist.id
  try {
    await api.addPlaylistTracks(playlist.id, [props.songId])
    contains.value = { ...contains.value, [playlist.id]: true }
    toast(`已加入《${playlist.title}》`)
    emit('added')
  } catch (error) {
    toast(error?.message || '添加失败')
  } finally {
    adding.value = ''
  }
}
</script>

<template>
  <Teleport v-if="ready" to=".device">
    <transition name="scrim">
      <div v-if="open" class="scrim" @click.self="emit('close')">
        <div class="sheet" role="dialog" aria-modal="true" aria-label="添加到歌单">
          <span class="grip" aria-hidden="true"></span>
          <div class="head">
            <p class="title">添加到歌单</p>
            <span class="song">{{ songTitle }}</span>
          </div>

          <ul v-if="playlists.length" class="list">
            <li v-for="playlist in playlists" :key="playlist.id">
              <button
                type="button"
                class="row"
                :disabled="contains[playlist.id] || adding === playlist.id"
                @click="addTo(playlist)"
              >
                <span class="row__cover" :style="coverStyle(playlist.cover)"></span>
                <span class="row__text">
                  <span class="row__title">{{ playlist.title }}</span>
                  <span class="row__sub">{{ playlist.trackCount || 0 }} 首歌曲</span>
                </span>
                <span class="row__act">
                  <Icon v-if="contains[playlist.id]" name="check" :size="15" :stroke="2.4" />
                  <Icon v-else-if="adding === playlist.id" name="refresh" :size="14" />
                  <Icon v-else name="plus" :size="16" :stroke="2.1" />
                </span>
              </button>
            </li>
          </ul>
          <p v-else class="empty">还没有歌单，去「我的」创建一个吧</p>

          <button type="button" class="done" @click="emit('close')">完成</button>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.scrim {
  position: absolute;
  inset: 0;
  z-index: 78;
  background: rgba(43, 31, 26, 0.32);
  display: flex;
  align-items: flex-end;
  backdrop-filter: blur(2px);
}

.sheet {
  width: 100%;
  max-height: 76%;
  padding: 10px 16px calc(12px + env(safe-area-inset-bottom));
  border-radius: 28px 28px 0 0;
  background: #fffdf8;
  box-shadow: 0 -12px 40px rgba(43, 31, 26, 0.2);
  display: flex;
  flex-direction: column;
}

.grip {
  display: block;
  width: 40px;
  height: 4px;
  margin: 0 auto 12px;
  border-radius: 2px;
  background: var(--surface-soft);
  flex: 0 0 auto;
}

.head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex: 0 0 auto;
}

.title {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--ink);
}

.song {
  font-size: 12px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.list {
  flex: 1 1 auto;
  min-height: 0;
  margin-top: 10px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: none;
}

.list::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.row {
  width: 100%;
  height: 58px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  border-radius: 12px;
}

.row:active {
  background: var(--surface-soft);
}

.row:disabled {
  cursor: default;
}

.row__cover {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  flex: 0 0 auto;
  background-color: var(--surface-cover);
}

.row__text {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.row__title {
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.row__sub {
  font-size: 11px;
  line-height: 14px;
  color: var(--ink-sub);
}

.row__act {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--primary);
  background: rgba(224, 120, 86, 0.1);
}

.row:disabled .row__act {
  background: transparent;
  color: var(--ink-sub);
}

.empty {
  margin: 28px 0;
  text-align: center;
  font-size: 13px;
  color: var(--ink-sub);
}

.done {
  flex: 0 0 auto;
  width: 100%;
  height: 50px;
  margin-top: 10px;
  border-radius: 18px;
  background: var(--primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  box-shadow: var(--shadow-cta);
  transition: transform 0.16s ease;
}

.done:active {
  transform: scale(0.99);
}

.scrim-enter-active,
.scrim-leave-active {
  transition: opacity 0.2s ease;
}

.scrim-enter-from,
.scrim-leave-to {
  opacity: 0;
}

.scrim-enter-active .sheet,
.scrim-leave-active .sheet {
  transition: transform 0.26s cubic-bezier(0.32, 0.72, 0, 1);
}

.scrim-enter-from .sheet,
.scrim-leave-to .sheet {
  transform: translateY(100%);
}
</style>
