import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

/** 浏览器同源请求 `/yddm-api/*`，由 Vite 转发到 yddm，避免直连跨域（仅 dev / preview 进程内生效） */
const yddmApiProxy = {
  '/yddm-api': {
    target: 'https://api.yddm.com',
    changeOrigin: true,
    rewrite: (path: string) => {
      const next = path.replace(/^\/yddm-api/, '')
      return next === '' ? '/' : next
    },
  },
} as const

/** 抖音/小红书同步采集服务（默认内网 8765） */
const syncApiProxyTarget =
  (process.env.VITE_SYNC_API_BASE as string | undefined)?.trim().replace(/\/$/, '') ||
  'http://192.168.1.11:8765'

/** 采集服务 API：`/api/v1/*` → 8765（`/admin/set_discount` 走 YDDM `/yddm-api`） */
const syncApiProxy = {
  '/api/v1': {
    target: syncApiProxyTarget,
    changeOrigin: true,
  },
} as const

// https://vite.dev/config/
export default defineConfig({
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
