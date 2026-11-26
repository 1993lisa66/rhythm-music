<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import TrackRow from '@/components/TrackRow.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import PlaylistFormSheet from '@/components/PlaylistFormSheet.vue'
import AddTracksSheet from '@/components/AddTracksSheet.vue'
import { api } from '@/api/client'
import { refreshPlaylists } from '@/store/data'
import { current, enqueue, playSong, state } from '@/store/player'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'
import { goBack } from '@/utils/nav'

const route = useRoute()
const router = useRouter()

const sheet = ref(false)
/* 删除歌单需要在面板内二次确认，避免误触直接删掉整个歌单 */
const confirming = ref(false)
const editing = ref(false)
const adding = ref(false)
const submitting = ref(false)
const favorited = ref(false)
const playlist = ref(null)

const EMPTY = {
  id: '',
  title: '歌单',
  badge: '',
  creator: '',
  count: 0,
  trackCount: 0,
  durationText: '',
  desc: '',
  info: '',
  cover: '',
  tone: 'primary',
  owned: false,
  tracks: []
}

const detail = computed(() => playlist.value || EMPTY)
const tracks = computed(() => detail.value.tracks)
/* 只有自己的歌单能增删改，系统歌单保持只读 */
const owned = computed(() => detail.value.owned === true)

const trackIds = computed(() => tracks.value.map((t) => t.id))

/* 列表高度按曲目数撑开，避免固定 250px 把后面的歌裁掉 */
const canvasHeight = computed(() => Math.max(800, 476 + tracks.value.length * 52 + 96))

const load = async (id) => {
  if (!id) return
  try {
    playlist.value = await api.playlist(id)
  } catch (error) {
    // 歌单不存在（含别人的私有歌单）时提示后回退，不留空白页
    toast(error?.message || '歌单加载失败')
    playlist.value = null
  }
}

const syncLists = async () => {
  try {
    await refreshPlaylists()
  } catch {
    // 列表同步失败不影响详情页操作结果
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

const back = () => goBack(router, '/discover')

onMounted(() => load(route.params.id))
/* 从上个歌单直接跳到另一个歌单时组件会复用，需按 id 重新拉取 */
watch(() => route.params.id, (id) => load(id))

const actions = computed(() => {
  const list = [
    { key: 'queue', label: '添加到播放队列', icon: 'queue' },
    {
      key: 'favorite',
      label: favorited.value ? '取消收藏歌单' : '收藏歌单',
      icon: 'heart',
      active: favorited.value
    },
    { key: 'share', label: '分享歌单', icon: 'share' },
    { key: 'downloads', label: '查看离线下载', icon: 'download' }
  ]
  if (owned.value) {
    list.unshift({ key: 'add', label: '添加歌曲', icon: 'plus' })
    list.unshift({ key: 'edit', label: '编辑歌单', icon: 'note' })
    list.push({ key: 'delete', label: '删除歌单', icon: 'trash', danger: true })
  }
  return list
})

const sheetTitle = computed(() => (confirming.value ? '删除歌单？' : detail.value.title))

const sheetSubtitle = computed(() =>
  confirming.value
    ? `将删除《${detail.value.title}》及其中的 ${detail.value.count} 首歌，歌曲本身仍保留在曲库`
    : `${detail.value.creator} · ${detail.value.count} 首`
)

const sheetActions = computed(() =>
  confirming.value
    ? [
        { key: 'delete-confirm', label: '确认删除', icon: 'trash', danger: true },
        { key: 'keep', label: '保留歌单' }
      ]
    : actions.value
)

const openSheet = () => {
  confirming.value = false
  sheet.value = true
}

const removePlaylist = async () => {
  if (submitting.value) return
  submitting.value = true
  try {
    await api.deletePlaylist(detail.value.id)
    await syncLists()
    toast('歌单已删除')
    router.replace('/mylists')
  } catch (error) {
    toast(error?.message || '删除失败')
  } finally {
    submitting.value = false
  }
}

const saveEdit = async ({ title, desc }) => {
  if (submitting.value) return
  submitting.value = true
  try {
    playlist.value = await api.updatePlaylist(detail.value.id, { title, desc })
    editing.value = false
    await syncLists()
    toast('歌单已更新')
  } catch (error) {
    toast(error?.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

/* 弹层里每加一首都会触发，顺带刷新详情，让曲目数和时长实时跟上 */
const onTracksAdded = async () => {
  await load(detail.value.id)
  await syncLists()
}

const removeTrack = async (track) => {
  if (submitting.value) return
  submitting.value = true
  try {
    playlist.value = await api.removePlaylistTrack(detail.value.id, track.id)
    await syncLists()
    toast(`已移出《${track.title}》`)
  } catch (error) {
    toast(error?.message || '移出失败')
  } finally {
    submitting.value = false
  }
}

const onPick = async (key) => {
  if (key === 'keep') {
    confirming.value = false
    sheet.value = false
    return
  }
  if (key === 'delete') {
    confirming.value = true
    return
  }
  if (key === 'delete-confirm') {
    sheet.value = false
    confirming.value = false
    await removePlaylist()
    return
  }

  sheet.value = false
  if (key === 'edit') {
    editing.value = true
  } else if (key === 'add') {
    adding.value = true
  } else if (key === 'queue') {
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
    <div class="page__canvas" :style="{ height: `${canvasHeight}px` }">
      <button type="button" class="nav nav--back" aria-label="返回" @click="back">
        <Icon name="back" :size="22" :stroke="2" />
      </button>

      <button
        type="button"
        class="nav nav--more"
        aria-label="更多操作"
        aria-haspopup="dialog"
        @click="openSheet"
      >
        <Icon name="more" :size="22" />
      </button>

      <div class="hero" :style="coverStyle(detail.cover, 0.58)">
        <span class="hero__badge">{{ detail.badge }}</span>
        <span class="hero__note">
          <Icon name="note" :size="30" :stroke="1.5" />
        </span>
      </div>

      <h1 class="title">{{ detail.title }}</h1>
      <p class="info">{{ detail.creator }} · {{ detail.count }} 首歌曲 · {{ detail.durationText }}</p>
      <p class="desc">{{ detail.desc }}</p>

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
          :duration="t.duration"
          :active="current.id === t.id && state.playing"
          :removable="owned"
          @select="playTrack(t)"
          @remove="removeTrack(t)"
        />

        <div v-if="!tracks.length" class="tracks__empty">
          <Icon name="note" :size="22" :stroke="1.5" />
          <p class="tracks__empty-title">{{ owned ? '歌单还是空的' : '这个歌单还没有曲目' }}</p>
          <p v-if="owned" class="tracks__empty-sub">点右上角「更多 → 添加歌曲」开始挑选</p>
        </div>
      </div>
    </div>

    <ActionSheet
      :open="sheet"
      :title="sheetTitle"
      :subtitle="sheetSubtitle"
      :actions="sheetActions"
      @pick="onPick"
      @close="sheet = false"
    />

    <PlaylistFormSheet
      :open="editing"
      mode="edit"
      :initial-title="detail.title"
      :initial-desc="detail.desc"
      :submitting="submitting"
      @submit="saveEdit"
      @close="editing = false"
    />

    <AddTracksSheet
      :open="adding"
      :playlist-id="detail.id"
      :existing-ids="trackIds"
      @added="onTracksAdded"
      @close="adding = false"
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

/* 曲目列表 342 宽，高度随曲目数增长（画布高度同步计算） */
.tracks {
  position: absolute;
  left: 24px;
  top: 476px;
  width: 342px;
  min-height: 250px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 12px 0;
  overflow: hidden;
}

.tracks__empty {
  height: 226px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--placeholder);
}

.tracks__empty-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-sub);
}

.tracks__empty-sub {
  font-size: 12px;
  line-height: 17px;
  color: var(--placeholder);
}
</style>
