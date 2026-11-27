/** 秒 → mm:ss */
export function fmtTime(sec) {
  const total = Math.max(0, Math.floor(Number(sec) || 0))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/**
 * 秒 → 时长跨度文案（专辑 / 歌单总时长）
 * 不足 1 小时给「46 分钟」，否则「1.6 小时」，避免出现 95:44 这种像单曲时长的写法
 */
export function fmtSpan(sec) {
  const total = Math.max(0, Math.floor(Number(sec) || 0))
  if (total >= 3600) return `${(total / 3600).toFixed(1)} 小时`
  return `${Math.max(1, Math.round(total / 60))} 分钟`
}

/**
 * 封面背景：真实图片 + 可选日落渐变叠层
 * @param {string} src 图片地址
 * @param {number} overlay 渐变叠层透明度，0 表示纯图
 */
export function coverStyle(src, overlay = 0) {
  if (!src) return {}
  const graded =
    overlay > 0
      ? `linear-gradient(135deg, rgba(255,179,68,${overlay}) 0%, rgba(255,126,84,${overlay}) 50%, rgba(255,77,141,${overlay}) 100%), `
      : ''
  return {
    backgroundImage: `${graded}url("${src}")`,
    backgroundSize: 'cover',
    backgroundPosition: 'center'
  }
}

export const clamp = (v, min, max) => Math.min(max, Math.max(min, v))
