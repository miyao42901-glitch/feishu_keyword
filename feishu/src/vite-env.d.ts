/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * YDDM API 根地址（无末尾 `/`）。默认 `/yddm-api`（反代到 `https://api.yddm.com`）；直连时可填 `https://api.yddm.com`。
   */
  readonly VITE_YDDM_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
