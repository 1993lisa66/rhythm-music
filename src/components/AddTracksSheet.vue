<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import Icon from './Icon.vue'
import { api } from '@/api/client'
import { data } from '@/store/data'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  playlistId: { type: String, default: '' },
  existingIds: { type: Array, default: () => [] }
})

const emit = defineEmits(['added', 'close'])

const ready = ref(false)
const keyword = ref('')
const adding = ref('')
const addedCount = ref(0)
const included = reactive(new Set())

onMounted(() => {
  ready.value = true
})

watch(
  () => props.open,
  (open) => {
    if (!open) return
    keyword.value = ''
    adding.value = ''
    addedCount.value = 0
    included.clear()
    props.existingIds.forEach((id) => included.add(id))
  }
)

const results = computed(() => {
  const key = keyword.value.trim().toLowerCase()
  const list = key
    ? data.songs.filter((song) =>
        [song.title, song.artist, song.album].some((text) =>
          String(text || '').toLowerCase().includes(key)
        )
      )
    : data.songs
  return list.slice(0, 80)
})

const add = async (song) => {
  if (!props.playlistId || included.has(song.id) || adding.value) return
  adding.value = song.id
  try {
    await api.addPlaylistTracks(props.playlistId, [song.id])
    included.add(song.id)
    addedCount.value += 1
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
        <div class="sheet" role="dialog" aria-modal="true" aria-label="添加歌曲">
          <span class="grip" aria-hidden="true"></span>

          <div class="head">
            <p class="title">添加歌曲</p>
            <span class="count num">已添加 {{ addedCount }} 首</span>
          </div>

          <div class="search">
            <Icon name="search" :size="15" :stroke="1.9" />
            <input v-model="keyword" type="text" placeholder="搜索歌曲、歌手、专辑" />
          </div>

          <ul class="list">
            <li v-for="song in results" :key="song.id">
              <button
                type="button"
                class="row"
                :class="{ 'row--on': included.has(song.id) }"
                :disabled="included.has(song.id) || adding === song.id"
                @click="add(song)"
              >
                <span class="row__cover" :style="coverStyle(song.cover)"></span>
                <span class="row__text">
                  <span class="row__title">{{ song.title }}</span>
                  <span class="row__sub">{{ song.artist }}</span>
                </span>
                <span class="row__act">
                  <Icon v-if="included.has(song.id)" name="check" :size="15" :stroke="2.4" />
                  <Icon v-else-if="adding === song.id" name="refresh" :size="14" />
                  <Icon v-else name="plus" :size="16" :stroke="2.1" />
                </span>
              </button>
            </li>
          </ul>

          <p v-if="!results.length" class="empty">没有找到匹配的歌曲</p>

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
  z-index: 76;
  background: rgba(43, 31, 26, 0.32);
  display: flex;
  align-items: flex-end;
  backdrop-filter: blur(2px);
}

.sheet {
  width: 100%;
  height: 78%;
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
  flex: 0 0 auto;
}

.title {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--ink);
}

.count {
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-sub);
}

.search {
  margin-top: 12px;
  height: 42px;
  padding: 0 14px;
  border-radius: 14px;
  background: var(--surface-soft);
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--placeholder);
  flex: 0 0 auto;
}

.search input {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 14px;
  color: var(--ink);
}

.search input::placeholder {
  color: var(--placeholder);
}

.list {
  flex: 1 1 auto;
  min-height: 0;
  margin-top: 8px;
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
  height: 56px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  border-radius: 12px;
  transition: background 0.16s ease;
}

.row:active {
  background: var(--surface-soft);
}

.row:disabled {
  cursor: default;
}

.row__cover {
  width: 40px;
  height: 40px;
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
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
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

.row--on .row__title {
  color: var(--ink-sub);
}

.row--on .row__act {
  background: transparent;
}

.empty {
  margin-top: 24px;
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
