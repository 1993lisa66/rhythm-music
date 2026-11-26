<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import TrackRow from '@/components/TrackRow.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import playlists from '@/data/playlists.json'
import { current, enqueue, getSong, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'
import { goBack } from '@/utils/nav'

const route = useRoute()
const router = useRouter()

const sheet = ref(false)
const favorited = ref(false)

const playlist = computed(
  () => playlists.find((p) => p.id === route.params.id) || playlists[0]
)

const tracks = computed(() =>
  playlist.value.tracks.map((t) => {
    const song = getSong(t.id) || {}
    return { ...song, durationText: t.duration ?? song.duration }
  })
)

const trackIds = computed(() => tracks.value.map((t) => t.id))

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

const back = () => goBack(router, '/discover')

const actions = computed(() => [
  { key: 'queue', label: '添加到播放队列', icon: 'queue' },
  { key: 'favorite', label: favorited.value ? '取消收藏歌单' : '收藏歌单', icon: 'heart', active: favorited.value },
  { key: 'share', label: '分享歌单', icon: 'share' },
  { key: 'downloads', label: '查看离线下载', icon: 'download' }
])

const onPick = async (key) => {
  sheet.value = false
  if (key === 'queue') {
    const added = enqueue(trackIds.value)
    toast(added ? `已添加 ${added} 首到播放队列` : '队列里已经有这些歌了')
  } else if (key === 'favorite') {
    favorited.value = !favorited.value
    toast(favorited.value ? '已收藏歌单' : '已取消收藏')
  } else if (key === 'share') {
    try {
      await navigator.clipboard.writeText(window.location.href)
      toast('歌单链接已复制')
    } catch {
      toast('当前环境不支持复制链接')
    }
  } else if (key === 'downloads') {
    router.push('/downloads')
  }
}
</script>

<template>
  <div class="page">
    <div class="page__canvas">
      <button type="button" class="nav nav--back" aria-label="返回" @click="back">
        <Icon name="back" :size="22" :stroke="2" />
      </button>

      <button
        type="button"
        class="nav nav--more"
        aria-label="更多操作"
        aria-haspopup="dialog"
        @click="sheet = true"
      >
        <Icon name="more" :size="22" />
      </button>

      <div class="hero" :style="coverStyle(playlist.cover, 0.58)">
        <span class="hero__badge">{{ playlist.badge }}</span>
        <span class="hero__note">
          <Icon name="note" :size="30" :stroke="1.5" />
        </span>
      </div>

      <h1 class="title">{{ playlist.title }}</h1>
      <p class="info">{{ playlist.creator }} · {{ playlist.count }} 首歌曲 · {{ playlist.durationText }}</p>
      <p class="desc">{{ playlist.desc }}</p>

      <div class="actions">
        <button type="button" class="btn btn--primary" @click="playAll">
          <Icon name="play" :size="14" />
          <span>播放全部</span>
        </button>
        <button type="button" class="btn btn--ghost" @click="shuffleAll">随机播放</button>
      </div>

      <div class="tracks">
        <TrackRow
          v-for="(t, i) in tracks"
          :key="t.id + i"
          :index="i + 1"
          :title="t.title"
          :artist="t.artist"
          :duration="t.durationText"
          :active="current.id === t.id && state.playing"
          @select="playTrack(t)"
        />
      </div>
    </div>

    <ActionSheet
      :open="sheet"
      :title="playlist.title"
      :subtitle="`${playlist.creator} · ${playlist.count} 首`"
      :actions="actions"
      @pick="onPick"
      @close="sheet = false"
    />
  </div>
</template>

<style scoped>
.nav {
  position: absolute;
  top: 34px;
  width: 22px;
  height: 22px;
  color: var(--ink);
  display: grid;
  place-items: center;
  transition: color 0.16s ease, transform 0.16s ease;
}

.nav--back {
  left: 24px;
}

.nav--more {
  right: 24px;
}

.nav:hover {
  color: var(--primary);
}

/* 主封面 342 × 200 r24 */
.hero {
  position: absolute;
  left: 24px;
  top: 74px;
  width: 342px;
  height: 200px;
  border-radius: 24px;
  background-color: var(--primary);
  box-shadow: var(--shadow-cover);
  overflow: hidden;
}

.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(130% 100% at 12% 100%, rgba(43, 31, 26, 0.24), transparent 60%);
}

.hero__badge {
  position: absolute;
  left: 16px;
  top: 18px;
  height: 24px;
  padding: 0 10px;
  border-radius: var(--r-badge);
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  font-size: 11px;
  line-height: 24px;
  letter-spacing: 0.3px;
  z-index: 1;
  backdrop-filter: blur(4px);
}

.hero__note {
  position: absolute;
  left: 50%;
  top: 46px;
  transform: translateX(-50%);
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  display: grid;
  place-items: center;
  z-index: 1;
  backdrop-filter: blur(2px);
}

.title {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 294px;
  font-size: 24px;
  font-weight: 700;
  line-height: 32px;
  letter-spacing: -0.2px;
  color: var(--ink);
}

.info {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 332px;
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-sub);
}

.desc {
  position: absolute;
  left: 24px;
  right: 24px;
  top: 360px;
  font-size: 13px;
  line-height: 20px;
  color: var(--ink-sub);
}

/* 操作按钮 */
.actions {
  position: absolute;
  left: 24px;
  top: 404px;
  display: flex;
  gap: 12px;
}

.btn {
  height: 48px;
  border-radius: var(--r-btn);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.btn:active {
  transform: scale(0.97);
}

.btn--primary {
  width: 180px;
  background: var(--primary);
  color: #fff;
  box-shadow: var(--shadow-cta);
}

.btn--primary :deep(.ico) {
  transform: translateX(1px);
}

.btn--ghost {
  width: 150px;
  background: var(--surface);
  color: var(--primary);
  border: 1.5px solid var(--primary);
}

/* 曲目列表 342 × 250 */
.tracks {
  position: absolute;
  left: 24px;
  top: 476px;
  width: 342px;
  height: 250px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 12px 0;
  overflow: hidden;
}
</style>
