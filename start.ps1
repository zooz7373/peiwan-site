# peiwan.co 快速启动脚本
# 用法: .\start.ps1

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "peiwan.co 游戏内容矩阵站" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Host "[OK] Python: $(python --version)" -ForegroundColor Green
} else {
    Write-Host "[MISSING] Python 未安装" -ForegroundColor Red
}

# 检查 Git
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    Write-Host "[OK] Git: $(git --version)" -ForegroundColor Green
} else {
    Write-Host "[MISSING] Git 未安装" -ForegroundColor Red
}

# 检查 Hugo
$hugo = Get-Command hugo -ErrorAction SilentlyContinue
if ($hugo) {
    Write-Host "[OK] Hugo: $(hugo version)" -ForegroundColor Green
} else {
    Write-Host "[MISSING] Hugo 未安装" -ForegroundColor Red
    Write-Host "  运行 setup_server.ps1 会自动安装" -ForegroundColor Yellow
}

# 检查 API Key
$apiKey = $env:MIMO_API_KEY
if (-not $apiKey) {
    $apiKey = [System.Environment]::GetEnvironmentVariable("MIMO_API_KEY", "User")
}
if ($apiKey) {
    Write-Host "[OK] MIMO_API_KEY 已设置" -ForegroundColor Green
} else {
    Write-Host "[MISSING] MIMO_API_KEY 未设置" -ForegroundColor Red
    Write-Host "  设置方法: `$env:MIMO_API_KEY='your-key'" -ForegroundColor Yellow
}

# 检查 openai 包
$openai = pip show openai 2>$null
if ($openai) {
    Write-Host "[OK] openai 包已安装" -ForegroundColor Green
} else {
    Write-Host "[MISSING] openai 包未安装" -ForegroundColor Red
    Write-Host "  安装: pip install openai" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "快速操作" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "一键部署（首次）:" -ForegroundColor White
Write-Host "  .\scripts\setup_server.ps1 -ApiKey 'your-key'" -ForegroundColor Gray
Write-Host ""
Write-Host "安装定时任务:" -ForegroundColor White
Write-Host "  .\scripts\install_task.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "手动生成文章:" -ForegroundColor White
Write-Host "  python scripts\generate.py --limit 10" -ForegroundColor Gray
Write-Host ""
Write-Host "预览待生成:" -ForegroundColor White
Write-Host "  python scripts\generate.py --dry-run" -ForegroundColor Gray
Write-Host ""
Write-Host "本地预览站点（需要 Hugo）:" -ForegroundColor White
Write-Host "  cd site; hugo server -D" -ForegroundColor Gray
Write-Host ""
