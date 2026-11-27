<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import PlaylistFormSheet from '@/components/PlaylistFormSheet.vue'
import { api } from '@/api/client'
import { data, refreshPlaylists } from '@/store/data'
import { toast } from '@/store/toast'
import { coverStyle } from '@/utils/format'

const router = useRouter()

const playlists = computed(() => data.playlists)
const open = (p) => router.push(`/playlist/${p.id}`)

const creating = ref(false)
const submitting = ref(false)

const openCreate = () => {
  creating.value = true
}

const createPlaylist = async ({ title, desc }) => {
  if (submitting.value) return
  submitting.value = true
  try {
    const created = await api.createPlaylist({ title, desc })
    await refreshPlaylists()
    creating.value = false
    toast('歌单已创建')
    router.push(`/playlist/${created.id}`)
  } catch (error) {
    toast(error?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    await refreshPlaylists()
  } catch (error) {
    toast(error?.message || '加载歌单失败')
  }
})
</script>

<template>
  <div class="page">
    <div class="page__canvas mylists">
      <PageNav title="我的歌单" fallback="/profile">
        <template #right>
          <button type="button" class="new hit" @click="openCreate">
            <Icon name="plus" :size="14" :stroke="2.2" />
            <span>新建</span>
          </button>
        </template>
      </PageNav>

      <!-- 与「全部专辑」一致的 2 列封面网格 -->
      <div class="grid">
        <button v-for="p in playlists" :key="p.id" type="button" class="card" @click="open(p)">
          <span class="card__cover" :style="coverStyle(p.cover, 0.28)">
            <span class="card__count">{{ p.count }} 首</span>
          </span>
          <span class="card__title">{{ p.title }}</span>
          <span class="card__sub">{{ p.badge }} · {{ p.durationText }}</span>
        </button>
      </div>

      <p class="tip">共 {{ playlists.length }} 个歌单，点击进入查看曲目</p>
    </div>

    <PlaylistFormSheet
      :open="creating"
      mode="create"
      :submitting="submitting"
      @submit="createPlaylist"
      @close="creating = false"
    />
  </div>
</template>

<style scoped>
.mylists {
  height: auto;
  min-height: 800px;
  padding: 92px 24px 140px;
}

.new {
  height: 26px;
  padding: 0 10px;
  border-radius: 13px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  background: rgba(224, 120, 86, 0.1);
  transition: background 0.16s ease, transform 0.16s ease;
}

.new:active {
  transform: scale(0.96);
  background: rgba(224, 120, 86, 0.18);
}

/* 2 列网格：封面 152×116，与「全部专辑」同规格 */
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px 14px;
}

.card {
  min-width: 0;
  text-align: left;
  transition: transform 0.18s ease;
}

.card:active {
  transform: scale(0.98);
}

.card__cover {
  position: relative;
  display: block;
  width: 100%;
  aspect-ratio: 152 / 116;
  border-radius: var(--r-card);
  background-color: var(--surface-cover);
  box-shadow: 0 6px 16px rgba(224, 120, 86, 0.12);
  overflow: hidden;
}

.card__count {
  position: absolute;
  right: 10px;
  top: 10px;
  height: 20px;
  padding: 0 8px;
  border-radius: 10px;
  background: rgba(43, 31, 26, 0.34);
  color: #fff;
  font-size: 10px;
  line-height: 20px;
  backdrop-filter: blur(4px);
}

.card__title {
  display: block;
  margin-top: 10px;
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.card__sub {
  display: block;
  margin-top: 3px;
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-sub);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.tip {
  margin-top: 22px;
  font-size: 12px;
  line-height: 17px;
  color: var(--placeholder);
  text-align: center;
}
</style>
