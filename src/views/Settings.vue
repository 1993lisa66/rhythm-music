<script setup>
import { ref } from 'vue'
import Icon from '@/components/Icon.vue'
import PageNav from '@/components/PageNav.vue'
import Switch from '@/components/Switch.vue'
import ActionSheet from '@/components/ActionSheet.vue'
import { QUALITIES, settings, updateSetting } from '@/store/settings'
import { refreshDataSources } from '@/store/data'
import { syncPlayer } from '@/store/player'
import { toast } from '@/store/toast'

const picker = ref(false)
const sourcePicker = ref(false)
const cache = ref('12.4 MB')

const SOURCE_LABELS = { server: '服务器资源', oss: 'OSS' }

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

const clearCache = () => {
  if (cache.value === '0 B') {
    toast('缓存已经很干净了')
    return
  }
  cache.value = '0 B'
  toast('已清除 12.4 MB 缓存')
}
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
          <span class="row__value">ID: 8823 6102</span>
        </div>
      </div>
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
  min-height: 800px;
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
