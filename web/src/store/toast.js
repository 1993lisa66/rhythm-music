import { reactive } from 'vue'

export const toastState = reactive({ text: '', visible: false })

let timer = null

/** 轻提示：1.8s 自动消失，重复触发会重置计时 */
export function toast(text) {
  toastState.text = text
  toastState.visible = true
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    toastState.visible = false
  }, 1800)
}
