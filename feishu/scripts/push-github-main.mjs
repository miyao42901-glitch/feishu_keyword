/**
 * 将 public/feishu（dist/ + package.json + README.md）推到 GitHub 的 main 分支。
 * 该仓 main 仅作飞书插件静态发布，不含完整 monorepo；开发仍在 GitLab hxp。
 *
 * 前置：npm run build:github:test
 * 环境：GITHUB_REPO（默认 git@github.com:miyao42901-glitch/feishu_keyword.git）
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
const githubRepo =
  process.env.GITHUB_REPO?.trim() || 'git@github.com:miyao42901-glitch/feishu_keyword.git'

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
  run(`git commit -m "release(feishu): ${version} 测试包 dist 目录"`, tmp)
  run('git branch -M main', tmp)
  run(`git remote add origin ${githubRepo}`, tmp)
  run('git push -f origin main', tmp)

  try {
    run('git push origin --delete hxp', tmp)
  } catch {
    console.log('push-github-main: 远程无 hxp 分支或已删除，跳过')
  }

  console.log('push-github-main: 已更新 GitHub main（仅 dist/、package.json、README.md）')
} finally {
  rmSync(tmp, { recursive: true, force: true })
}
