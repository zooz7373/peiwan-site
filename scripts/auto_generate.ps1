# peiwan.co 自动内容生成脚本
# 由 Windows 计划任务定时调用
# 每天凌晨 3:00 运行，生成 10 篇文章并推送到 GitHub

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
if (-not $env:MIMO_MODEL) { $env:MIMO_MODEL = "mimo-v2-flash" }

# 生成 10 篇文章
Write-Log "开始生成文章..."
python "$PSScriptRoot\generate.py" --limit 10 --push
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Log "文章生成完成"
} else {
    Write-Log "[WARN] 文章生成过程中有错误 (exit code: $exitCode)"
}

# 构建 Hugo（验证无错误）
Write-Log "构建 Hugo..."
hugo -s "$repoDir\site" --minify --quiet 2>&1 | ForEach-Object { Write-Log $_ }

if ($?) {
    Write-Log "Hugo 构建成功"
} else {
    Write-Log "[WARN] Hugo 构建失败"
}

# 推送（如果 generate.py 没有推送的话）
Write-Log "推送到 GitHub..."
git -C $repoDir add .
$status = git -C $repoDir status --porcelain
if ($status) {
    git -C $repoDir commit -m "feat: 自动新增内容 $(Get-Date -Format 'yyyy-MM-dd')"
    git -C $repoDir push
    Write-Log "已推送到 GitHub"
} else {
    Write-Log "没有新变更需要推送"
}

Write-Log "========== 自动生成完成 =========="
