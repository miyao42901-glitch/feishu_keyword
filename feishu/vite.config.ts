import path from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { DEFAULT_YDDM_UPSTREAM_ORIGIN } from './src/lib/yddm-api'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

/** YDDM 开发代理上游（仅 Vite；与浏览器请求的 `/yddm-api` 分离） */
function resolveYddmProxyTarget(env: Record<string, string>): string {
  const proxyTarget = env.YDDM_PROXY_TARGET?.trim()
  if (proxyTarget) return proxyTarget.replace(/\/$/, '')
  const viteBase = env.VITE_YDDM_API_BASE?.trim()
  if (viteBase && /^https?:\/\//i.test(viteBase)) return viteBase.replace(/\/$/, '')
  return DEFAULT_YDDM_UPSTREAM_ORIGIN
}

/** 抖音/小红书同步采集服务（仓根 SYNC_PROXY_TARGET / VITE_SYNC_API_BASE） */
function resolveSyncApiProxyTarget(env: Record<string, string>): string {
  const sync = env.SYNC_PROXY_TARGET?.trim()
  if (sync) return sync.replace(/\/$/, '')
  const viteSync = env.VITE_SYNC_API_BASE?.trim()
  if (viteSync) return viteSync.replace(/\/$/, '')
  return 'http://127.0.0.1:8765'
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 代理目标读仓根 .env / .env.local（须在 config 内 loadEnv，顶层 process.env 拿不到 .env.local）
  const env = loadEnv(mode, repoRoot, '')

  const yddmApiProxyTarget = resolveYddmProxyTarget(env)
  const syncApiProxyTarget = resolveSyncApiProxyTarget(env)

  if (mode === 'development') {
    console.log('[vite] proxy /api/v1 →', syncApiProxyTarget)
    console.log('[vite] proxy /yddm-api →', yddmApiProxyTarget)
  }

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

  const syncApiProxy = {
    '/api/v1': {
      target: syncApiProxyTarget,
      changeOrigin: true,
    },
  } as const

  return {
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
  }
})
