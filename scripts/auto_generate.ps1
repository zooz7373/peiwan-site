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
python "$PSScriptRoot\generate.py"
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Log "文章生成完成"
} else {
    Write-Log "[WARN] 文章生成过程中有错误 (exit code: $exitCode)"
}

# 清空旧文件再构建，防止缓存残留
Write-Log "Clearing C:\www\peiwan..."
Remove-Item -Path C:\www\peiwan\* -Recurse -Force -ErrorAction SilentlyContinue

# 构建 Hugo 并部署到 Nginx
Write-Log "Building Hugo site..."
hugo -s "$repoDir\site" --minify --destination C:\www\peiwan 2>&1 | ForEach-Object { Write-Log $_ }

if ($?) {
    Write-Log "Site deployed to C:\www\peiwan"
} else {
    Write-Log "[WARN] Hugo build failed"
}

# 仅本地部署，不同步 GitHub

# 重启 Nginx
Write-Log "Restarting Nginx..."
Get-Process nginx -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process "C:\nginx-1.27.5\nginx.exe" -WorkingDirectory "C:\nginx-1.27.5"
Write-Log "Nginx restarted"

Write-Log "========== Auto generation complete =========="
