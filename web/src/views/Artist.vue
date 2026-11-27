<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import TrackRow from '@/components/TrackRow.vue'
import { api } from '@/api/client'
import { current, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const artist = ref(null)
const loading = ref(true)

const decode = (value) => {
  try {
    return decodeURIComponent(value || '')
  } catch {
    return value || ''
  }
}
const name = computed(() => decode(route.params.name))
const tracks = computed(() => artist.value?.tracks || [])
const trackIds = computed(() => tracks.value.map((t) => t.id))
const meta = computed(() => {
  const info = artist.value
  if (!info) return ''
  const parts = [`${info.songCount} 首歌曲`]
  if (info.albumCount) parts.push(`${info.albumCount} 张专辑`)
  if (info.durationText) parts.push(info.durationText)
  return parts.join(' · ')
})

const load = async (value) => {
  if (!value) return
  loading.value = true
  try {
    artist.value = await api.artist(value)
  } catch (error) {
    artist.value = null
    toast(error?.message || '歌手加载失败')
  } finally {
    loading.value = false
  }
}

const playAll = () => {
  if (trackIds.value.length) playSong(trackIds.value[0], trackIds.value)
}

const shuffleAll = () => {
  const ids = trackIds.value.slice()
  for (let i = ids.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[ids[i], ids[j]] = [ids[j], ids[i]]
  }
  if (ids.length) playSong(ids[0], ids)
}

const playTrack = (t) => playSong(t.id, trackIds.value)
const openAlbum = (album) => {
  if (album) router.push(`/album/${encodeURIComponent(album)}`)
}

onMounted(() => load(name.value))
watch(name, (value) => load(value))
</script>

<template>
  <div class="page">
    <div class="page__canvas artist">
      <PageNav title="歌手" fallback="/discover" />

      <div class="hero">
        <span class="hero__avatar" :style="coverStyle(artist?.cover)">
          <Icon v-if="!artist?.cover" name="mic" :size="34" :stroke="1.5" />
        </span>
        <div class="hero__text">
          <h1 class="hero__name">{{ artist?.name || name }}</h1>
          <p class="hero__meta num">{{ meta }}</p>
        </div>
      </div>

      <div class="actions">
        <button type="button" class="btn btn--primary" :disabled="!tracks.length" @click="playAll">
          <Icon name="play" :size="14" />
          <span>播放全部</span>
        </button>
        <button type="button" class="btn btn--ghost" :disabled="!tracks.length" @click="shuffleAll">
          随机播放
        </button>
      </div>

      <div v-if="tracks.length" class="tracks">
        <p class="tracks__label">全部歌曲</p>
        <TrackRow
          v-for="(t, i) in tracks"
          :key="t.id"
          :index="i + 1"
          :title="t.title"
          :artist="t.album || t.artist"
          :duration="t.duration"
          :active="current.id === t.id && state.playing"
          @select="playTrack(t)"
        />
      </div>

      <div v-else-if="!loading" class="empty">
        <span class="empty__icon"><Icon name="mic" :size="24" :stroke="1.6" /></span>
        <p class="empty__title">没有找到这位歌手的歌曲</p>
        <p class="empty__sub">曲库里暂时没有收录</p>
      </div>

      <button
        v-if="tracks.length"
        type="button"
        class="album-link"
        @click="openAlbum(tracks[0].album)"
      >
        <Icon name="note" :size="16" :stroke="1.7" />
        <span>查看所属专辑「{{ tracks[0].album }}」</span>
        <Icon name="chevron" :size="13" :stroke="1.8" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.artist {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 150px;
}

/* 歌手头图：圆形头像 + 名称 */
.hero {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero__avatar {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  flex: 0 0 auto;
  background-color: var(--surface-cover);
  background-size: cover;
  background-position: center;
  color: var(--primary);
  display: grid;
  place-items: center;
  box-shadow: var(--shadow-cover);
}

.hero__text {
  min-width: 0;
  flex: 1 1 auto;
}

.hero__name {
  font-size: 24px;
  font-weight: 700;
  line-height: 32px;
  letter-spacing: -0.2px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.hero__meta {
  margin-top: 6px;
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-sub);
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.btn {
  height: 46px;
  border-radius: var(--r-btn);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  transition: transform 0.16s ease;
}

.btn:active {
  transform: scale(0.97);
}

.btn:disabled {
  opacity: 0.5;
}

.btn--primary {
  flex: 1 1 auto;
  background: var(--primary);
  color: #fff;
  box-shadow: var(--shadow-cta);
}

.btn--ghost {
  width: 132px;
  background: var(--surface);
  color: var(--primary);
  border: 1.5px solid var(--primary);
}

.tracks {
  margin-top: 22px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 6px 0 8px;
  overflow: hidden;
}

.tracks__label {
  padding: 10px 16px 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-sub);
}

.album-link {
  margin-top: 16px;
  width: 100%;
  height: 52px;
  padding: 0 16px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--ink-sub);
  text-align: left;
}

.album-link span {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: var(--ink);
}

.empty {
  margin-top: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--placeholder);
}

.empty__icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--surface-soft);
  display: grid;
  place-items: center;
  color: var(--primary);
}

.empty__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-sub);
}

.empty__sub {
  font-size: 12px;
  color: var(--placeholder);
}
</style>
