# peiwan.co 自动内容生成脚本
# 由 Windows 计划任务定时调用
# 每天凌晨 3:00 运行，按游戏权重分配生成文章并推送到 GitHub

$ErrorActionPreference = "Continue"

$repoDir = Split-Path -Parent $PSScriptRoot
$logFile = "$PSScriptRoot\auto_generate.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File -Append -FilePath $logFile -Encoding utf8
    Write-Host "$timestamp $Message"
}

Write-Log "========== 开始自动生成 =========="

# 加载环境变量
$apiKey = [System.Environment]::GetEnvironmentVariable("MIMO_API_KEY", "User")
if (-not $apiKey) {
    Write-Log "[ERROR] MIMO_API_KEY 未设置"
    exit 1
}
$env:MIMO_API_KEY = $apiKey
$env:MIMO_API_BASE = [System.Environment]::GetEnvironmentVariable("MIMO_API_BASE", "User")
if (-not $env:MIMO_API_BASE) { $env:MIMO_API_BASE = "https://token-plan-cn.xiaomimimo.com/anthropic" }
$env:MIMO_MODEL = [System.Environment]::GetEnvironmentVariable("MIMO_MODEL", "User")
if (-not $env:MIMO_MODEL) { $env:MIMO_MODEL = "mimo-v2.5-pro" }

# 按游戏权重生成文章（默认 8 篇，由 generate.py 内部 GAME_WEIGHTS 控制）
Write-Log "开始按权重生成文章..."
python "$PSScriptRoot\generate.py" --push
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Log "文章生成完成"
} else {
    Write-Log "[WARN] 文章生成过程中有错误 (exit code: $exitCode)"
}

# 构建 Hugo 并部署到 Nginx
Write-Log "Building Hugo site..."
hugo -s "$repoDir\site" --minify --destination C:\www\peiwan 2>&1 | ForEach-Object { Write-Log $_ }

if ($?) {
    Write-Log "Site deployed to C:\www\peiwan"
} else {
    Write-Log "[WARN] Hugo build failed"
}

# 推送（如果 generate.py 没有推送的话）
Write-Log "Pushing to GitHub..."
git -C $repoDir add .
$status = git -C $repoDir status --porcelain
if ($status) {
    git -C $repoDir commit -m "feat: auto content update $(Get-Date -Format 'yyyy-MM-dd')"
    git -C $repoDir push
    Write-Log "Pushed to GitHub"
} else {
    Write-Log "No changes to push"
}

Write-Log "========== Auto generation complete =========="
