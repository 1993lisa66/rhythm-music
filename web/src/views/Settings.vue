<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import Switch from '@/components/Switch.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import { QUALITIES, settings, updateSetting } from '@/store/settings'
import { auth, logout } from '@/store/auth'
import { refreshDataSources } from '@/store/data'
import { syncPlayer } from '@/store/player'
import { toast } from '@/store/toast'

const router = useRouter()
const picker = ref(false)
const sourcePicker = ref(false)
const signingOut = ref(false)
const cacheBytes = ref(0)

const SOURCE_LABELS = { server: '服务器资源', oss: 'OSS' }

const fmtBytes = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`
  return `${bytes} B`
}
const cache = ref('0 B')

/* 缓存大小取浏览器真实占用，不再写死数字 */
const refreshCache = async () => {
  let usage = 0
  try {
    const estimate = await navigator.storage?.estimate?.()
    usage = estimate?.usage || 0
  } catch {
    usage = 0
  }
  if (!usage) {
    try {
      usage = Object.keys(window.localStorage).reduce(
        (sum, key) => sum + key.length + (window.localStorage.getItem(key) || '').length,
        0
      )
    } catch {
      usage = 0
    }
  }
  cacheBytes.value = usage
  cache.value = fmtBytes(usage)
}

const qualityActions = () =>
  QUALITIES.map((q) => ({ key: q, label: q, active: settings.quality === q }))

const chooseQuality = async (key) => {
  try {
    await updateSetting({ quality: key })
    toast(`音质已切换为「${key}」`)
  } catch (error) {
    toast(error?.message || '切换音质失败')
  }
  picker.value = false
}

const sourceActions = () =>
  Object.entries(SOURCE_LABELS).map(([key, label]) => ({
    key,
    label,
    active: settings.assetSource === key
  }))

const chooseSource = async (key) => {
  sourcePicker.value = false
  try {
    await updateSetting({ assetSource: key })
    // 数据源变了，重新拉一次曲库和播放态让新的音频/封面地址生效
    await Promise.all([refreshDataSources(), syncPlayer()])
    toast(`数据源已切换为「${SOURCE_LABELS[key]}」`)
  } catch (error) {
    toast(error?.message || '切换数据源失败')
  }
}

/* 只清真正的缓存：Cache Storage + 非登录态的本地点位，登录 token 保留 */
const clearCache = async () => {
  if (!cacheBytes.value) {
    toast('当前没有可清理的缓存')
    return
  }
  const before = cache.value
  try {
    if (window.caches?.keys) {
      const keys = await window.caches.keys()
      await Promise.all(keys.map((key) => window.caches.delete(key)))
    }
    Object.keys(window.localStorage)
      .filter((key) => key.startsWith('rhythm.') && key !== 'rhythm.token' && key !== 'rhythm.lastEmail')
      .forEach((key) => window.localStorage.removeItem(key))
    await refreshCache()
    toast(`已清理 ${before} 缓存`)
  } catch {
    toast('清理缓存失败')
  }
}

/* 退出登录：api 失效也不阻塞，本地会话一定清掉 */
const confirmLogout = () => {
  signingOut.value = true
}
const doLogout = async () => {
  signingOut.value = false
  await logout()
  router.replace({ name: 'login' })
}
const logoutActions = [
  { key: 'keep', label: '继续使用' },
  { key: 'logout', label: '退出登录', danger: true }
]

onMounted(refreshCache)
</script>

<template>
  <div class="page">
    <div class="page__canvas settings">
      <PageNav title="设置" fallback="/profile" />

      <p class="group-label">播放</p>
      <div class="group">
        <button type="button" class="row" @click="picker = true">
          <span class="row__icon"><Icon name="note" :size="19" :stroke="1.8" /></span>
          <span class="row__name">音质</span>
          <span class="row__value">{{ settings.quality }}</span>
          <Icon class="row__chevron" name="chevron" :size="14" :stroke="1.8" />
        </button>

        <div class="row">
          <span class="row__icon"><Icon name="quote" :size="19" :stroke="1.8" /></span>
          <span class="row__name">播放页显示歌词</span>
          <Switch v-model="settings.showLyrics" label="播放页显示歌词" />
        </div>
      </div>

      <p class="group-label">存储</p>
      <div class="group">
        <button type="button" class="row" @click="sourcePicker = true">
          <span class="row__icon"><Icon name="download" :size="19" :stroke="1.8" /></span>
          <span class="row__name">数据源</span>
          <span class="row__value">{{ SOURCE_LABELS[settings.assetSource] }}</span>
          <Icon class="row__chevron" name="chevron" :size="14" :stroke="1.8" />
        </button>

        <button type="button" class="row" @click="clearCache">
          <span class="row__icon"><Icon name="trash" :size="19" :stroke="1.8" /></span>
          <span class="row__name">清除缓存</span>
          <span class="row__value num">{{ cache }}</span>
          <Icon class="row__chevron" name="chevron" :size="14" :stroke="1.8" />
        </button>
      </div>

      <p class="group-label">关于</p>
      <div class="group">
        <div class="row">
          <span class="row__icon"><Icon name="info" :size="19" :stroke="1.8" /></span>
          <span class="row__name">版本</span>
          <span class="row__value num">1.0.0</span>
        </div>
        <div class="row">
          <span class="row__icon"><Icon name="user" :size="19" :stroke="1.8" /></span>
          <span class="row__name">账号</span>
          <span class="row__value">{{ auth.user?.id || '—' }}</span>
        </div>
      </div>

      <button type="button" class="logout" @click="confirmLogout">退出登录</button>
    </div>

    <ActionSheet
      :open="picker"
      title="选择音质"
      subtitle="音质越高，流量消耗越大"
      :actions="qualityActions()"
      @pick="chooseQuality"
      @close="picker = false"
    />

    <ActionSheet
      :open="signingOut"
      title="退出登录"
      subtitle="退出后需要重新登录才能看到自己的歌单和收藏"
      :actions="logoutActions"
      @pick="(key) => (key === 'logout' ? doLogout() : (signingOut = false))"
      @close="signingOut = false"
    />

    <ActionSheet
      :open="sourcePicker"
      title="选择数据源"
      subtitle="服务器资源：从本站加载；OSS：从对象存储加载"
      :actions="sourceActions()"
      @pick="chooseSource"
      @close="sourcePicker = false"
    />
  </div>
</template>

<style scoped>
.settings {
  height: auto;
  min-height: 100%;
  padding: 92px 24px 140px;
}

.group-label {
  margin: 0 0 8px 4px;
  font-size: 12px;
  font-weight: 600;
  line-height: 16px;
  letter-spacing: 0.3px;
  color: var(--ink-sub);
}

.group {
  margin-bottom: 22px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  padding: 4px 0;
  overflow: hidden;
}

/* 退出登录：单独一条，靠颜色与普通设置项区分 */
.logout {
  width: 100%;
  height: 52px;
  margin-top: 4px;
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  font-size: 15px;
  font-weight: 600;
  color: #c4543f;
  transition: transform 0.16s ease;
}

.logout:active {
  transform: scale(0.985);
}

.row {
  width: 100%;
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.row + .row {
  box-shadow: inset 0 1px 0 rgba(43, 31, 26, 0.045);
}

button.row:active {
  background: rgba(245, 239, 227, 0.66);
}

.row__icon {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--surface-soft);
  color: var(--primary);
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}

.row__name {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 18px;
  color: var(--ink);
  white-space: nowrap;
}

.row__value {
  font-size: 13px;
  color: var(--ink-sub);
  white-space: nowrap;
  flex: 0 0 auto;
}

.row__chevron {
  color: var(--placeholder);
  flex: 0 0 auto;
}
</style>
