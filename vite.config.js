import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
const LOCAL_API_TARGET = process.env.VITE_LOCAL_API_TARGET || 'https://feishu.jzl.com'
const LOCAL_API_REWRITE_PREFIX = process.env.VITE_LOCAL_API_REWRITE_PREFIX || '/api/v1/public'
const DIRECT_API_TARGET = process.env.VITE_DIRECT_API_TARGET || 'https://www.dajiala.com'

export default defineConfig({
  server: {
    host: true,
    proxy: {
      '/api/v1/public': {
        target: LOCAL_API_TARGET,
        changeOrigin: true,
        proxyTimeout: 10_000,
        timeout: 10_000,
        rewrite: (path) => path.replace(/^\/api\/v1\/public/, LOCAL_API_REWRITE_PREFIX),
        configure: (proxy) => {
          proxy.on('error', (err, req) => {
            console.error(`[vite proxy] ${req.method} ${req.url} -> ${LOCAL_API_TARGET} failed:`, err.message)
          })
        },
      },
      '/direct-api': {
        target: DIRECT_API_TARGET,
        changeOrigin: true,
        proxyTimeout: 10_000,
        timeout: 10_000,
        rewrite: (path) => path.replace(/^\/direct-api/, ''),
        configure: (proxy) => {
          proxy.on('error', (err, req) => {
            console.error(`[vite proxy] ${req.method} ${req.url} -> ${DIRECT_API_TARGET} failed:`, err.message)
          })
        },
      },
    },
  },
  base: './',
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
