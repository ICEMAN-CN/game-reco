/**
 * 图片代理工具 - 解决 CORS 问题
 */

/**
 * 检查 URL 是否需要代理
 * 如果 URL 是外部域名，需要通过代理访问
 */
function needsProxy(url: string | undefined | null): boolean {
  if (!url) return false
  
  // 如果是相对路径或同源 URL，不需要代理
  if (url.startsWith('/') || url.startsWith('data:')) {
    return false
  }
  
  try {
    const urlObj = new URL(url)
    // 如果是 localhost 或同源，不需要代理
    const hostname = urlObj.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === window.location.hostname) {
      return false
    }
    // 其他外部域名需要代理
    return true
  } catch {
    // 无效的 URL，返回 false
    return false
  }
}

/**
 * 获取代理后的图片 URL
 * @param url 原始图片 URL
 * @returns 代理后的 URL 或原始 URL
 */
export function getProxiedImageUrl(url: string | undefined | null): string | undefined {
  if (!url) return undefined
  
  // 如果不需要代理，直接返回原 URL
  if (!needsProxy(url)) {
    return url
  }
  
  // 使用代理端点
  const encodedUrl = encodeURIComponent(url)
  return `/api/v1/images/proxy?url=${encodedUrl}`
}
