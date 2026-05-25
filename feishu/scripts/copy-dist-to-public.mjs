/**
 * 将 feishu/dist 同步到仓库根 public/feishu（Docker nginx / 手动推 GitHub）。
 */
import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const feishuRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(feishuRoot, '..')
const distDir = path.join(feishuRoot, 'dist')
const targetDir = path.join(repoRoot, 'public', 'feishu')

if (!existsSync(distDir)) {
  console.error('copy-dist-to-public: feishu/dist 不存在，请先 npm run build')
  process.exit(1)
}

mkdirSync(path.join(repoRoot, 'public'), { recursive: true })
if (existsSync(targetDir)) {
  rmSync(targetDir, { recursive: true, force: true })
}
mkdirSync(targetDir, { recursive: true })
cpSync(distDir, targetDir, { recursive: true })
console.log('copy-dist-to-public: 已同步到', targetDir)
