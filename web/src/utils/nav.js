/**
 * 子页返回：有历史记录时回退，直接深链进入时回落到主 Tab，
 * 避免 router.back() 把用户弹出应用。
 */
export function goBack(router, fallback = '/discover') {
  const state = window.history.state
  if (state && state.back) router.back()
  else router.replace(fallback)
}
