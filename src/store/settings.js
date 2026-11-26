import { reactive, watch } from 'vue'

const KEY = 'rhythm.settings'

const read = () => {
  try {
    return JSON.parse(window.localStorage.getItem(KEY) || '{}')
  } catch {
    return {}
  }
}

const saved = read()

export const QUALITIES = ['标准', '高品质', '无损']

/** 设置项持久化到 localStorage，刷新后仍然生效 */
export const settings = reactive({
  quality: QUALITIES.includes(saved.quality) ? saved.quality : '高品质',
  wifiOnly: typeof saved.wifiOnly === 'boolean' ? saved.wifiOnly : true,
  showLyrics: typeof saved.showLyrics === 'boolean' ? saved.showLyrics : true
})

watch(
  settings,
  (value) => {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(value))
    } catch {
      /* 无痕模式写入失败不影响使用 */
    }
  },
  { deep: true }
)
