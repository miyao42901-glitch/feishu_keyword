/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly PROD: boolean
  readonly DEV: boolean
  /** 覆盖管理端默认 API 基址（生产构建 axios baseURL） */
  readonly VITE_ADMIN_API_ORIGIN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
