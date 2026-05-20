/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 根地址，如 `http://127.0.0.1:8000`（不含 `/api`） */
  readonly VITE_API_BASE_URL?: string
  /**
   * YDDM API 根地址（无末尾 `/`）。默认 `http://192.168.1.11:8001`；dev 未设时走 `/yddm-api` 代理。
   */
  readonly VITE_YDDM_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
