/**
 * 后端 API 客户端。
 * - 自动带上 Authorization: Bearer <token>
 * - 统一解析后端的 {"error": {code, message}} 错误体
 * - 401 时通知上层（auth store）清理登录态并跳登录页
 */

const BASE = import.meta.env.VITE_API_BASE || '/api/v1'
const TOKEN_KEY = 'rhythm.token'

let token = ''
try {
  token = window.localStorage.getItem(TOKEN_KEY) || ''
} catch {
  token = ''
}

export function getToken() {
  return token
}

export function setToken(next) {
  token = next || ''
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token)
    else window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* 无痕模式写入失败不影响本次会话 */
  }
}

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

let onUnauthorized = () => {}
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

export async function request(path, { method = 'GET', body, auth = true, signal } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body)
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new ApiError(0, 'network_error', '无法连接服务器，请确认后端已启动')
  }

  if (response.status === 204) return null

  const text = await response.text()
  let payload = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = null
    }
  }

  if (!response.ok) {
    const detail = payload?.error || {}
    const error = new ApiError(
      response.status,
      detail.code || 'http_error',
      detail.message || `请求失败（${response.status}）`
    )
    if (response.status === 401 && auth && !path.startsWith('/auth/')) onUnauthorized(error)
    throw error
  }

  return payload
}

const qs = (params = {}) => {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const api = {
  // 账号
  register: (body) => request('/auth/register', { method: 'POST', body, auth: false }),
  login: (body) => request('/auth/login', { method: 'POST', body, auth: false }),
  me: () => request('/auth/me'),
  patchMe: (body) => request('/auth/me', { method: 'PATCH', body }),
  logout: () => request('/auth/logout', { method: 'POST' }),

  // 内容
  songs: (params) => request(`/songs${qs(params)}`),
  deleteSong: (songId) =>
    request(`/songs/${encodeURIComponent(songId)}`, { method: 'DELETE' }),
  lyrics: (songId) => request(`/songs/${encodeURIComponent(songId)}/lyrics`, { auth: false }),
  fetchLyrics: (songId) =>
    request(`/songs/${encodeURIComponent(songId)}/lyrics/fetch`, { method: 'POST' }),
  playlists: () => request('/playlists'),
  playlist: (id) => request(`/playlists/${encodeURIComponent(id)}`),
  createPlaylist: (body) => request('/playlists', { method: 'POST', body }),
  updatePlaylist: (id, body) =>
    request(`/playlists/${encodeURIComponent(id)}`, { method: 'PATCH', body }),
  deletePlaylist: (id) =>
    request(`/playlists/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  addPlaylistTracks: (id, songIds) =>
    request(`/playlists/${encodeURIComponent(id)}/tracks`, {
      method: 'POST',
      body: { songIds }
    }),
  removePlaylistTrack: (id, songId) =>
    request(
      `/playlists/${encodeURIComponent(id)}/tracks/${encodeURIComponent(songId)}`,
      { method: 'DELETE' }
    ),
  discover: () => request('/discover'),
  library: () => request('/library'),
  albums: () => request('/library/albums'),
  album: (name) => request(`/library/albums/${encodeURIComponent(name)}`),
  artist: (name) => request(`/artists/${encodeURIComponent(name)}`),
  search: (params) => request(`/search${qs(params)}`),
  hot: () => request('/search/hot'),
  refreshHot: () => request('/search/hot/refresh', { method: 'POST' }),
  recommend: () => request('/search/recommend'),

  // 资源：私有 Bucket 地址有有效期，到期前用旧地址换新签名
  signAssets: (paths) => request('/assets/sign', { method: 'POST', body: { paths } }),

  // 播放器
  player: () => request('/player'),
  play: (body) => request('/player/play', { method: 'POST', body }),
  toggle: () => request('/player/toggle', { method: 'POST' }),
  next: (auto = false) => request(`/player/next${auto ? '?auto=true' : ''}`, { method: 'POST' }),
  prev: () => request('/player/prev', { method: 'POST' }),
  seek: (body) => request('/player/seek', { method: 'POST', body }),
  progress: (body) => request('/player/progress', { method: 'PUT', body }),
  shuffle: () => request('/player/shuffle', { method: 'POST' }),
  repeat: () => request('/player/repeat', { method: 'POST' }),
  queue: () => request('/player/queue'),
  enqueue: (songIds) => request('/player/queue', { method: 'POST', body: { songIds } }),
  removeFromQueue: (position) =>
    request(`/player/queue/${position}`, { method: 'DELETE' }),
  clearQueue: () => request('/player/queue', { method: 'DELETE' }),

  // 用户数据
  favorites: () => request('/favorites'),
  toggleFavorite: (songId) =>
    request(`/favorites/${encodeURIComponent(songId)}/toggle`, { method: 'POST' }),
  recent: () => request('/recent'),
  clearRecent: () => request('/recent', { method: 'DELETE' }),

  // 我的
  profile: () => request('/me/profile'),
  myPlaylists: () => request('/me/playlists'),
  settings: () => request('/me/settings'),
  patchSettings: (body) => request('/me/settings', { method: 'PATCH', body })
}
