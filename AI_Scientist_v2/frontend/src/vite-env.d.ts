/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 基址：web/PWA 留空走同源相对路径；打包为原生 App 时设为 http://<host>:8000 */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
