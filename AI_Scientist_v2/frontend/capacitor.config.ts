import type { CapacitorConfig } from '@capacitor/cli'

/**
 * Capacitor 原生 App 配置。
 * - webDir 指向前端构建产物 dist（先 npm run build，再 npx cap sync）。
 * - 打包前需在 frontend/.env 设 VITE_API_BASE=http://<后端IP或域名>:8000，
 *   否则 webview 里的相对 /api 打不到后端（webview origin 不是后端域名）。
 */
const config: CapacitorConfig = {
  appId: 'com.zhixing.aiscientist',
  appName: '智研星枢',
  webDir: 'dist',
  android: {
    allowMixedContent: true, // 允许 http 后端与内置 https 资源混用（局域网调试用）
  },
  server: {
    androidScheme: 'http', // 直连局域网 http 后端时避免 https 混用被拦截
  },
}

export default config
