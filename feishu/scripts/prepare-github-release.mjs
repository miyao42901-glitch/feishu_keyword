/**
 * 将 feishu/dist 同步到 GitHub 发布仓目录下的 dist/（与 inconelx 等飞书插件仓结构一致）：
 *   <github-repo>/
 *     dist/
 *       assets/
 *       index.html
 *       favicon.svg | favicon.ico
 *       jzl_icon.png
 *     package.json
 *     README.md
 *
 * 默认目标：仓库根 public/feishu（需先 git clone GitHub 空仓到此目录）
 * 覆盖：环境变量 GITHUB_RELEASE_DIR
 */
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const feishuRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(feishuRoot, '..')
const distDir = path.join(feishuRoot, 'dist')
const releaseRoot = process.env.GITHUB_RELEASE_DIR?.trim()
  ? path.resolve(process.env.GITHUB_RELEASE_DIR)
  : path.join(repoRoot, 'public', 'feishu')
const targetDist = path.join(releaseRoot, 'dist')

if (!existsSync(distDir)) {
  console.error('prepare-github-release: feishu/dist 不存在，请先 npm run build')
  process.exit(1)
}

mkdirSync(releaseRoot, { recursive: true })

/** 发布仓根目录只保留 dist/、package.json、README、.git 等；删掉旧版扁平 assets、index.html */
const keepAtReleaseRoot = new Set([
  '.git',
  'dist',
  'package.json',
  'README.md',
  'readme.md',
  '.gitignore',
])
for (const name of readdirSync(releaseRoot)) {
  if (keepAtReleaseRoot.has(name)) continue
  const p = path.join(releaseRoot, name)
  rmSync(p, { recursive: true, force: true })
  console.log('prepare-github-release: 已删除发布仓根目录多余项', name)
}

if (existsSync(targetDist)) {
  rmSync(targetDist, { recursive: true, force: true })
}
mkdirSync(targetDist, { recursive: true })
cpSync(distDir, targetDist, { recursive: true })

/** 飞书插件仓根目录常见图标（参考 jzl 发布仓） */
const iconSources = [
  { from: path.join(feishuRoot, 'public', 'jzl_icon.png'), to: 'jzl_icon.png' },
  { from: path.join(feishuRoot, 'public', 'custom.png'), to: 'jzl_icon.png' },
]
for (const { from, to } of iconSources) {
  const dest = path.join(targetDist, to)
  if (!existsSync(dest) && existsSync(from)) {
    cpSync(from, dest)
    break
  }
}

const faviconIco = path.join(feishuRoot, 'public', 'favicon.ico')
const faviconSvg = path.join(feishuRoot, 'public', 'favicon.svg')
if (existsSync(faviconIco)) {
  cpSync(faviconIco, path.join(targetDist, 'favicon.ico'))
} else if (existsSync(faviconSvg) && !existsSync(path.join(targetDist, 'favicon.ico'))) {
  cpSync(faviconSvg, path.join(targetDist, 'favicon.svg'))
}

const pkgPath = path.join(feishuRoot, 'package.json')
const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'))
const githubPkgPath = path.join(releaseRoot, 'package.json')
const githubPkg = {
  name: 'feishu-keyword',
  version: pkg.version ?? '0.0.0',
  private: true,
  description: '飞书关键词监控插件静态资源（dist/）',
}
writeFileSync(githubPkgPath, `${JSON.stringify(githubPkg, null, 2)}\n`, 'utf8')

const readmePath = path.join(releaseRoot, 'README.md')
if (!existsSync(readmePath)) {
  writeFileSync(
    readmePath,
    `# 飞书关键词监控插件\n\n静态资源目录为 \`dist/\`，由主仓 \`feishu_keyword\` 执行 \`npm run build:github:test\` 生成。\n`,
    'utf8',
  )
}

console.log('prepare-github-release: 已写入', targetDist)
console.log('prepare-github-release: package.json ->', githubPkgPath)
console.log('prepare-github-release: 发布仓根目录应仅有 dist/、package.json、README.md：')
for (const name of readdirSync(releaseRoot).sort()) {
  console.log('  -', name)
}
