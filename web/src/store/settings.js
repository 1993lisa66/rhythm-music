/** 播放设置：存在服务端（每个用户一份），这里做本地镜像。 */

import { reactive } from 'vue'
import { api } from '@/api/client'

export const QUALITIES = ['标准', '高品质', '无损']

export const settings = reactive({
  quality: '高品质',
  showLyrics: true,
  // 资源数据源：server=服务器本地静态文件，oss=私有 Bucket 签名地址
  assetSource: 'server'
})

function apply(payload) {
  if (!payload) return
  settings.quality = payload.quality
  settings.showLyrics = !!payload.showLyrics
  settings.assetSource = payload.assetSource || 'server'
}

export function applySettings(payload) {
  apply(payload)
}

export function resetSettings() {
  apply({ quality: '高品质', showLyrics: true, assetSource: 'server' })
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
