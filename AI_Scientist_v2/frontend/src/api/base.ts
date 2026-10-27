/**
 * 统一的 API 基址。
 * - Web / PWA：留空 → 走同源相对路径（/api/...），行为与之前完全一致。
 * - 原生 App（Capacitor）：webview origin 不是后端域名，需在 .env 设 VITE_API_BASE=http://<后端IP>:8000。
 * 所有直接拼 URL 的地方（img src / EventSource / 裸 fetch）都应前缀本常量。
 */
export const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/+$/, '')

/** 给相对 API 路径加上基址前缀（幂等：已是绝对 URL 则原样返回） */
export function apiUrl(path: string): string {
  if (/^(https?:)?\/\//.test(path)) return path
  return `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`
}
