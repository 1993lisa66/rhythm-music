/** 播放设置：存在服务端（每个用户一份），这里做本地镜像。 */

import { reactive } from 'vue'
import { api } from '@/api/client'

export const QUALITIES = ['标准', '高品质', '无损']

export const settings = reactive({
  quality: '高品质',
  showLyrics: true
})

function apply(payload) {
  if (!payload) return
  settings.quality = payload.quality
  settings.showLyrics = !!payload.showLyrics
}

export function applySettings(payload) {
  apply(payload)
}

export function resetSettings() {
  apply({ quality: '高品质', showLyrics: true })
}

export async function loadSettings() {
  const payload = await api.settings()
  apply(payload)
  return payload
}

/** 只提交变化的字段，失败时回滚到服务端值 */
export async function updateSetting(patch) {
  const snapshot = { ...settings }
  Object.assign(settings, patch)
  try {
    apply(await api.patchSettings(patch))
    return true
  } catch (error) {
    Object.assign(settings, snapshot)
    throw error
  }
}
