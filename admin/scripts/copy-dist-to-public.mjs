/**
 * 将 admin/dist 同步到仓库根 public/admin（供 Docker nginx 挂载与 Git 提交）。
 * 由 npm run build:public 调用；需先已成功执行 vite build。
 */
import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '..')
const distDir = path.join(adminRoot, 'dist')
const targetDir = path.join(repoRoot, 'public', 'admin')

if (!existsSync(distDir)) {
  console.error('copy-dist-to-public: admin/dist 不存在，请先执行 npm run build')
  process.exit(1)
}

mkdirSync(path.join(repoRoot, 'public'), { recursive: true })
if (existsSync(targetDir)) {
  rmSync(targetDir, { recursive: true, force: true })
}
mkdirSync(targetDir, { recursive: true })
cpSync(distDir, targetDir, { recursive: true })
console.log('copy-dist-to-public: 已同步到', targetDir)
