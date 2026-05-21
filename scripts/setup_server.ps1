# peiwan.co 服务器一键部署脚本
# 在 Windows 服务器上运行一次即可
# 用法: 以管理员身份运行 PowerShell，执行 .\scripts\setup_server.ps1

param(
    [string]$ApiKey,
    [string]$ApiBase = "https://token-plan-cn.xiaomimimo.com/anthropic",
    [string]$Model = "mimo-v2-flash",
    [string]$RepoUrl = ""
)

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "peiwan.co 服务器部署脚本" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: 检查/安装依赖 ──────────────────────────────

Write-Host "[1/6] 检查依赖..." -ForegroundColor Yellow

# Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "  [!] Python 未安装，请先安装 Python 3.10+" -ForegroundColor Red
    Write-Host "  下载: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] Python: $(python --version)" -ForegroundColor Green

# pip install anthropic
Write-Host "  安装 anthropic 包..." -ForegroundColor Gray
pip install anthropic --quiet 2>$null
Write-Host "  [OK] anthropic 已安装" -ForegroundColor Green

# Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "  [!] Git 未安装，请先安装 Git" -ForegroundColor Red
    Write-Host "  下载: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] Git: $(git --version)" -ForegroundColor Green

# Hugo
$hugo = Get-Command hugo -ErrorAction SilentlyContinue
if (-not $hugo) {
    Write-Host "  安装 Hugo..." -ForegroundColor Gray
    $hasScoop = Get-Command scoop -ErrorAction SilentlyContinue
    if ($hasScoop) {
        scoop install hugo-extended
    } else {
        $hasWinget = Get-Command winget -ErrorAction SilentlyContinue
        if ($hasWinget) {
            winget install Hugo.Hugo.Extended --accept-package-agreements --accept-source-agreements
        } else {
            Write-Host "  [!] 无法自动安装 Hugo，请手动安装" -ForegroundColor Red
            Write-Host "  下载: https://github.com/gohugoio/hugo/releases" -ForegroundColor Yellow
            exit 1
        }
    }
}
Write-Host "  [OK] Hugo 已就绪" -ForegroundColor Green

# ── Step 2: 配置环境变量 ──────────────────────────────

Write-Host ""
Write-Host "[2/6] 配置 API 密钥..." -ForegroundColor Yellow

if (-not $ApiKey) {
    $ApiKey = Read-Host "  请输入 MiMo API Key"
}

# 保存到系统环境变量（永久）
[System.Environment]::SetEnvironmentVariable("MIMO_API_KEY", $ApiKey, "User")
[System.Environment]::SetEnvironmentVariable("MIMO_API_BASE", $ApiBase, "User")
[System.Environment]::SetEnvironmentVariable("MIMO_MODEL", $Model, "User")

# 当前会话也设置
$env:MIMO_API_KEY = $ApiKey
$env:MIMO_API_BASE = $ApiBase
$env:MIMO_MODEL = $Model

Write-Host "  [OK] 环境变量已保存" -ForegroundColor Green

# ── Step 3: Git 配置 ──────────────────────────────

Write-Host ""
Write-Host "[3/6] 配置 Git..." -ForegroundColor Yellow

$repoDir = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$repoDir\.git")) {
    Write-Host "  初始化 Git 仓库..." -ForegroundColor Gray
    git init $repoDir
    git -C $repoDir add .
    git -C $repoDir commit -m "feat: 初始化 peiwan.co 站点"
}

if ($RepoUrl) {
    # 检查是否已添加 remote
    $remotes = git -C $repoDir remote
    if (-not $remotes) {
        git -C $repoDir remote add origin $RepoUrl
        Write-Host "  [OK] 远程仓库已添加: $RepoUrl" -ForegroundColor Green
    }
    git -C $repoDir branch -M main
    git -C $repoDir push -u origin main
    Write-Host "  [OK] 已推送到 GitHub" -ForegroundColor Green
} else {
    Write-Host "  [i] 未指定远程仓库，请稍后手动添加:" -ForegroundColor Yellow
    Write-Host "      git remote add origin https://github.com/你的用户名/peiwan-site.git" -ForegroundColor Gray
}

# ── Step 4: 安装 PaperMod 主题 ──────────────────────────────

Write-Host ""
Write-Host "[4/6] 安装 Hugo 主题..." -ForegroundColor Yellow

$themeDir = "$repoDir\site\themes\PaperMod"
if (-not (Test-Path $themeDir)) {
    git submodule add --depth=1 https://github.com/adityatelange/hugo-PaperMod.git $themeDir 2>$null
    if ($?) {
        Write-Host "  [OK] PaperMod 主题已安装" -ForegroundColor Green
    } else {
        # 备选：直接 clone
        git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git $themeDir 2>$null
        Write-Host "  [OK] PaperMod 主题已安装 (clone)" -ForegroundColor Green
    }
} else {
    Write-Host "  [OK] PaperMod 主题已存在" -ForegroundColor Green
}

# ── Step 5: 测试 Hugo 构建 ──────────────────────────────

Write-Host ""
Write-Host "[5/6] 测试 Hugo 构建..." -ForegroundColor Yellow

hugo -s "$repoDir\site" --minify --quiet
if ($?) {
    Write-Host "  [OK] Hugo 构建成功" -ForegroundColor Green
} else {
    Write-Host "  [!] Hugo 构建失败，请检查配置" -ForegroundColor Red
}

# ── Step 6: 测试内容生成 ──────────────────────────────

Write-Host ""
Write-Host "[6/6] 测试内容生成 (1 篇)..." -ForegroundColor Yellow

python "$repoDir\scripts\generate.py" --limit 1
if ($?) {
    Write-Host "  [OK] 内容生成测试通过" -ForegroundColor Green
} else {
    Write-Host "  [!] 内容生成失败，请检查 API 配置" -ForegroundColor Red
}

# ── 完成 ──────────────────────────────

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步:" -ForegroundColor White
Write-Host "  1. 安装定时任务: .\scripts\install_task.ps1" -ForegroundColor Gray
Write-Host "  2. 连接 Cloudflare Pages（从 GitHub 自动部署）" -ForegroundColor Gray
Write-Host "  3. 注册 Google AdSense" -ForegroundColor Gray
Write-Host ""
