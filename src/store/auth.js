/** 登录态：token 存在 localStorage，用户资料来自 /auth/me。 */

import { computed, reactive } from 'vue'
import { api, getToken, setToken, setUnauthorizedHandler } from '@/api/client'
import { resetData } from './data'

export const auth = reactive({
  user: null,
  ready: false
})

export const isLoggedIn = computed(() => !!auth.user)

/** 记住上一次登录的邮箱，方便再次登录 */
const LAST_EMAIL_KEY = 'rhythm.lastEmail'
export const lastEmail = () => {
  try {
    return window.localStorage.getItem(LAST_EMAIL_KEY) || ''
  } catch {
    return ''
  }
}
const rememberEmail = (email) => {
  try {
    window.localStorage.setItem(LAST_EMAIL_KEY, email)
  } catch {
    /* 忽略 */
  }
}

export function clearSession() {
  setToken('')
  auth.user = null
  resetData()
}

setUnauthorizedHandler(() => {
  if (!auth.user) return
  clearSession()
  import('@/router')
    .then(({ default: router }) => {
      const current = router.currentRoute.value
      if (current.name !== 'login') {
        router.replace({ name: 'login', query: { redirect: current.fullPath } })
      }
    })
    .catch(() => {})
})

let booting = null

/** 应用启动时恢复登录态；401 视为未登录，不打断页面渲染 */
export function bootstrap() {
  if (booting) return booting
  booting = (async () => {
    if (getToken()) {
      try {
        auth.user = await api.me()
      } catch {
        setToken('')
        auth.user = null
      }
    }
    auth.ready = true
    return auth.user
  })()
  return booting
}

export async function login(email, password) {
  const result = await api.login({ email, password })
  setToken(result.token)
  auth.user = result.user
  rememberEmail(email)
  return result.user
}

export async function register(email, password, name) {
  const result = await api.register({ email, password, name })
  setToken(result.token)
  auth.user = result.user
  rememberEmail(email)
  return result.user
}

export async function logout() {
  try {
    await api.logout()
  } catch {
    /* 令牌可能已过期，忽略即可 */
  }
  clearSession()
}
