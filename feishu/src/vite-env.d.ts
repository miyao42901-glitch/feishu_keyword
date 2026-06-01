/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * YDDM API 根地址（无末尾 `/`）。默认 `/yddm-api`（反代到 `https://api.yddm.com`）；直连时可填 `https://api.yddm.com`。
   * 飞书插件 CDN（`ext.baseopendev.com`）发版须填绝对地址，如 `https://test-fskw-feishu.tbpf.com/yddm-api`。
   */
  readonly VITE_YDDM_API_BASE?: string
  /**
   * 采集 API 根地址（无末尾 `/`）。默认空字符串，走同源 `/api/v1/...`。
   * 飞书插件 CDN 发版须填绝对地址，如 `https://test-fskw-feishu.tbpf.com`。
   */
  readonly VITE_SYNC_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
