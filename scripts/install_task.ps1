# 安装 Windows 计划任务
# 每天凌晨 3:00 自动生成内容并推送
# 用法: 以管理员身份运行 .\scripts\install_task.ps1

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "安装计划任务" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$taskName = "PeiwanAutoGenerate"
$scriptPath = "$PSScriptRoot\auto_generate.ps1"

# 删除已存在的任务
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  已删除旧任务" -ForegroundColor Yellow
}

# 创建任务触发器：每天凌晨 3:00
$trigger = New-ScheduledTaskTrigger -Daily -At "03:00"

# 创建任务操作
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# 创建任务设置
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# 注册任务
Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Description "peiwan.co 每日自动生成游戏攻略内容" `
    -RunLevel Highest

Write-Host ""
Write-Host "[OK] 计划任务已安装" -ForegroundColor Green
Write-Host "  任务名: $taskName" -ForegroundColor Gray
Write-Host "  执行时间: 每天凌晨 3:00" -ForegroundColor Gray
Write-Host "  脚本: $scriptPath" -ForegroundColor Gray
Write-Host ""
Write-Host "手动触发测试:" -ForegroundColor White
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "查看任务状态:" -ForegroundColor White
Write-Host "  Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host ""
