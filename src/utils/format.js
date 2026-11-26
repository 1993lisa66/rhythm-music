/** 秒 → mm:ss */
export function fmtTime(sec) {
  const total = Math.max(0, Math.floor(Number(sec) || 0))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
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
