import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..')

function resolveAdminApiProxyTarget(env: Record<string, string>): string {
  const admin = env.VITE_ADMIN_API_ORIGIN?.trim().replace(/\/$/, '')
  if (admin) return admin
  const sync = env.SYNC_PROXY_TARGET?.trim().replace(/\/$/, '')
  if (sync) return sync
  const host = env.API_PUBLIC_HOST?.trim().replace(/^https?:\/\//, '').replace(/\/$/, '')
  if (host) return `https://${host}`
  return 'https://test-fskw.tbpf.com'
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, '')
  const adminApiProxyTarget = resolveAdminApiProxyTarget(env)

  return {
  envDir: repoRoot,
  base: '/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.join(__dirname, 'src'),
    },
  },
  server: {
    host: true,
    port: 5101,
    proxy: {
      '/api': {
        target: adminApiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
  },
  }
})
