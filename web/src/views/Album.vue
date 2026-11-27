<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import TrackRow from '@/components/TrackRow.vue'
import { api } from '@/api/client'
import { current, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle, fmtSpan } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const album = ref(null)
const loading = ref(true)

const decode = (value) => {
  try {
    return decodeURIComponent(value || '')
  } catch {
    return value || ''
  }
}
const name = computed(() => decode(route.params.name))
const tracks = computed(() => album.value?.tracks || [])
const trackIds = computed(() => tracks.value.map((t) => t.id))

const totalText = computed(() => {
  const info = album.value
  if (!info) return ''
  return `${info.songCount} 首 · ${fmtSpan(info.duration)}`
})

const load = async (value) => {
  if (!value) return
  loading.value = true
  try {
    album.value = await api.album(value)
  } catch (error) {
    album.value = null
    toast(error?.message || '专辑加载失败')
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
const openArtist = (artist) => {
  if (artist) router.push(`/artist/${encodeURIComponent(artist)}`)
}

onMounted(() => load(name.value))
watch(name, (value) => load(value))
</script>

<template>
  <div class="page">
    <div class="page__canvas album">
      <PageNav title="专辑" fallback="/library" />

      <div class="hero">
        <span class="hero__cover" :style="coverStyle(album?.cover)">
          <Icon v-if="!album?.cover" name="note" :size="30" :stroke="1.5" />
        </span>
        <div class="hero__text">
          <h1 class="hero__name">{{ album?.name || name }}</h1>
          <button type="button" class="hero__artist" @click="openArtist(album?.artist)">
            <span>{{ album?.artist || '群星' }}</span>
            <Icon name="chevron" :size="12" :stroke="1.8" />
          </button>
          <p class="hero__meta num">
            {{ totalText }}<template v-if="album?.year"> · {{ album.year }}</template>
          </p>
        </div>
      </div>

      <p v-if="album?.desc" class="desc">{{ album.desc }}</p>

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
        <TrackRow
          v-for="(t, i) in tracks"
          :key="t.id"
          :index="i + 1"
          :title="t.title"
          :artist="t.artist"
          :duration="t.duration"
          :active="current.id === t.id && state.playing"
          @select="playTrack(t)"
        />
      </div>

      <div v-else-if="!loading" class="empty">
        <span class="empty__icon"><Icon name="note" :size="24" :stroke="1.6" /></span>
        <p class="empty__title">这张专辑还没有曲目</p>
        <p class="empty__sub">换个专辑看看</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.album {
  height: auto;
  min-height: 100%;
  padding: 92px 24px 150px;
}

.hero {
  display: flex;
  gap: 16px;
}

.hero__cover {
  width: 112px;
  height: 112px;
  border-radius: var(--r-card);
  flex: 0 0 auto;
  background-color: var(--surface-cover);
  background-size: cover;
  background-position: center;
  color: var(--primary);
  display: grid;
  place-items: center;
  box-shadow: var(--shadow-cover);
  overflow: hidden;
}

.hero__text {
  min-width: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}

.hero__name {
  font-size: 20px;
  font-weight: 700;
  line-height: 27px;
  letter-spacing: -0.2px;
  color: var(--ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hero__artist {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  height: 24px;
  padding: 0 10px;
  border-radius: 12px;
  background: var(--sunset-soft);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  max-width: 100%;
}

.hero__artist span {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.hero__meta {
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-sub);
}

.desc {
  margin-top: 16px;
  font-size: 13px;
  line-height: 21px;
  color: var(--ink-sub);
}

.actions {
  margin-top: 18px;
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
