import { reactive } from 'vue'

export const toastState = reactive({
  text: '',
  visible: false,
  actionLabel: '',
  action: null
})

let timer = null

/**
 * 轻提示。
 * 默认 1.8s 自动消失；传 actionLabel + action 时变成「可撤销」提示，
 * 停留 5s，用户能在消失前把破坏性操作收回来。
 */
export function toast(text, options = {}) {
  toastState.text = text
  toastState.actionLabel = options.actionLabel || ''
  toastState.action = typeof options.action === 'function' ? options.action : null
  toastState.visible = true

  if (timer) clearTimeout(timer)
  const duration = options.duration || (toastState.action ? 5000 : 1800)
  timer = setTimeout(() => {
    toastState.visible = false
    toastState.action = null
    toastState.actionLabel = ''
  }, duration)
}

/** 点「撤销」时调用 */
export function runToastAction() {
  const fn = toastState.action
  if (timer) clearTimeout(timer)
  toastState.visible = false
  toastState.action = null
  toastState.actionLabel = ''
  if (fn) fn()
}

/** 主动收起（离开页面时用，避免撤销按钮留在别的页面上） */
export function hideToast() {
  if (timer) clearTimeout(timer)
  toastState.visible = false
  toastState.action = null
  toastState.actionLabel = ''
}
