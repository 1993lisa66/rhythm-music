<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageNav from '@/components/PageNav.vue'
import { api } from '@/api/client'
import { toast } from '@/store/toast'
import { coverStyle, fmtSpan } from '@/utils/format'

const router = useRouter()

const albums = ref([])
const loading = ref(true)

const total = computed(() =>
  albums.value.reduce((sum, a) => sum + (Number(a.songCount) || 0), 0)
)

const open = (album) => {
  if (album?.name) router.push(`/album/${encodeURIComponent(album.name)}`)
}

onMounted(async () => {
  try {
    const payload = await api.albums()
    albums.value = payload.items || []
  } catch (error) {
    toast(error?.message || '加载专辑失败')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <div class="page__canvas albums">
      <PageNav title="全部专辑" fallback="/library">
        <template #right>
          <span class="count num">{{ albums.length }} 张 · {{ total }} 首</span>
        </template>
      </PageNav>

      <div v-if="albums.length" class="grid">
        <button
          v-for="a in albums"
          :key="a.name"
          type="button"
          class="card"
          @click="open(a)"
        >
          <span class="card__cover" :style="coverStyle(a.cover)">
            <span class="card__count">{{ a.songCount }} 首</span>
          </span>
          <span class="card__title">{{ a.name }}</span>
          <span class="card__sub">{{ fmtSpan(a.duration) }}<template v-if="a.year"> · {{ a.year }}</template></span>
        </button>
      </div>

      <p v-if="albums.length" class="tip">共 {{ albums.length }} 张专辑，点击进入查看曲目</p>

      <div v-else-if="!loading" class="empty">
        <p class="empty__title">还没有专辑</p>
        <p class="empty__sub">曲库里还没有带专辑信息的歌曲</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.albums {
  height: auto;
  min-height: 100%;
  padding: 92px 24px 150px;
}

.count {
  font-size: 13px;
  line-height: 22px;
  color: var(--ink-sub);
}

/* 2 列网格：封面 152×116，与乐库「我的歌单」卡片同规格 */
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

.empty {
  margin-top: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--placeholder);
}

.empty__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-sub);
}

.empty__sub {
  font-size: 12px;
}
</style>
