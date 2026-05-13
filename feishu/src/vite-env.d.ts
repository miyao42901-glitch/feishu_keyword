/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 根地址，如 `http://127.0.0.1:8000`（不含 `/api`） */
  readonly VITE_API_BASE_URL?: string
  /**
   * yddm 计费 API 根地址（无末尾 `/`）。不设时：开发环境用 `/yddm-api`（Vite 代理）；生产用 `https://api.yddm.com`。
   */
  readonly VITE_YDDM_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
