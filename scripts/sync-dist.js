import { rmSync, cpSync, mkdirSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const src = resolve(root, 'dist')
const dest = resolve(root, 'dajialaFeishuPlugin/dist')

if (!existsSync(src)) {
  console.error('[sync-dist] dist 不存在，请先执行 npm run build')
  process.exit(1)
}

rmSync(dest, { recursive: true, force: true })
mkdirSync(dirname(dest), { recursive: true })
cpSync(src, dest, { recursive: true })

console.log(`[sync-dist] 已同步到 ${dest}`)
