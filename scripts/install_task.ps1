# Install Windows scheduled task
# Runs daily at 3:00 AM to auto-generate content
# Usage: Run as administrator: .\scripts\install_task.ps1

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Install Scheduled Task" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

$taskName = "PeiwanAutoGenerate"
$scriptPath = "$PSScriptRoot\auto_generate.ps1"

# Remove existing task
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "  Removed old task" -ForegroundColor Yellow
}

# Create trigger: daily at 3:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At "03:00"

# Create action
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $PSScriptRoot

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# Register task
Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Description "peiwan.co daily auto-generate game guides" `
    -RunLevel Highest

Write-Host ""
Write-Host "[OK] Scheduled task installed" -ForegroundColor Green
Write-Host "  Task: $taskName" -ForegroundColor Gray
Write-Host "  Time: Daily at 3:00 AM" -ForegroundColor Gray
Write-Host "  Script: $scriptPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Manual trigger:" -ForegroundColor White
Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "Check status:" -ForegroundColor White
Write-Host "  Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
Write-Host ""
