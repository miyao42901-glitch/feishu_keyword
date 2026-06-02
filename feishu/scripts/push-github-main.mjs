/**
 * 将 public/feishu（dist/ + package.json + README.md）推到插件发布仓。
 *
 * 前置：npm run build:github:prod（或 build:github:test）
 * 环境：
 *   PLUGIN_GIT_REMOTE — 默认 origin（GitLab jzl/feishu_keyword）
 *   PLUGIN_GIT_BRANCH — 默认 main
 *   GITHUB_REPO — 兼容旧变量，覆盖 PLUGIN_GIT_REMOTE
 */
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))
const feishuRoot = join(__dirname, '..')
const repoRoot = join(feishuRoot, '..')
const releaseDir = join(repoRoot, 'public', 'feishu')
const pluginRemote =
  process.env.GITHUB_REPO?.trim() ||
  process.env.PLUGIN_GIT_REMOTE?.trim() ||
  'http://192.168.1.200:8080/jzl/feishu_keyword.git'
const pluginBranch = process.env.PLUGIN_GIT_BRANCH?.trim() || 'main'

function run(cmd, cwd) {
  console.log(`> ${cmd}`)
  execSync(cmd, { cwd, stdio: 'inherit' })
}

for (const name of ['dist', 'package.json', 'README.md']) {
  if (!existsSync(join(releaseDir, name))) {
    console.error(`push-github-main: 缺少 ${releaseDir}/${name}，请先 npm run build:github:test`)
    process.exit(1)
  }
}

const tmp = mkdtempSync(join(tmpdir(), 'feishu-github-main-'))
try {
  cpSync(join(releaseDir, 'dist'), join(tmp, 'dist'), { recursive: true })
  cpSync(join(releaseDir, 'package.json'), join(tmp, 'package.json'))
  cpSync(join(releaseDir, 'README.md'), join(tmp, 'README.md'))

  const version = JSON.parse(readFileSync(join(releaseDir, 'package.json'), 'utf8')).version
  run('git init', tmp)
  run('git add dist package.json README.md', tmp)
  run(`git commit -m "release(feishu): ${version} 正式包 dist 目录"`, tmp)
  run(`git branch -M ${pluginBranch}`, tmp)
  run(`git remote add origin ${pluginRemote}`, tmp)
  run(`git push -f origin ${pluginBranch}`, tmp)

  console.log(`push-github-main: 已更新 ${pluginRemote} 分支 ${pluginBranch}（dist/、package.json、README.md）`)
} finally {
  rmSync(tmp, { recursive: true, force: true })
}
