import path from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { DEFAULT_YDDM_UPSTREAM_ORIGIN } from './src/lib/yddm-api'

/** YDDM 开发代理上游（仅 Vite；与浏览器请求的 `/yddm-api` 分离） */
function resolveYddmProxyTarget(): string {
  const proxyTarget = process.env.YDDM_PROXY_TARGET?.trim()
  if (proxyTarget) return proxyTarget.replace(/\/$/, '')
  const viteBase = (process.env.VITE_YDDM_API_BASE as string | undefined)?.trim()
  if (viteBase && /^https?:\/\//i.test(viteBase)) return viteBase.replace(/\/$/, '')
  return DEFAULT_YDDM_UPSTREAM_ORIGIN
}

/** YDDM：`/yddm-api/*` → YDDM 上游（去掉 `/yddm-api` 前缀） */
const yddmApiProxyTarget = resolveYddmProxyTarget()

const yddmApiProxy = {
  '/yddm-api': {
    target: yddmApiProxyTarget,
    changeOrigin: true,
    rewrite: (path: string) => {
      const next = path.replace(/^\/yddm-api/, '')
      return next === '' ? '/' : next
    },
  },
} as const

/** 抖音/小红书同步采集服务（仓根 SYNC_PROXY_TARGET 或 VITE_SYNC_API_BASE） */
const syncApiProxyTarget =
  process.env.SYNC_PROXY_TARGET?.trim().replace(/\/$/, '') ||
  (process.env.VITE_SYNC_API_BASE as string | undefined)?.trim().replace(/\/$/, '') ||
  'http://127.0.0.1:8765'

/** 采集服务 API：`/api/v1/*` → 8765（YDDM 登录/计费等走 `/yddm-api`） */
const syncApiProxy = {
  '/api/v1': {
    target: syncApiProxyTarget,
    changeOrigin: true,
  },
} as const

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

// https://vite.dev/config/
export default defineConfig({
  envDir: repoRoot,
  // 飞书自定义插件 / 扩展从非根路径加载静态资源时需要相对路径
  base: './',
  server: {
    host: true,
    // 内网穿透域名访问时放行 Host，否则 Vite 会 403（Blocked request）
    allowedHosts: ['.ngrok-free.app', '.ngrok-free.dev', '.ngrok.io', '.loca.lt'],
    proxy: { ...yddmApiProxy, ...syncApiProxy },
  },
  preview: {
    proxy: { ...yddmApiProxy, ...syncApiProxy },
  },
  plugins: [
    vue(),
    tailwindcss(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
