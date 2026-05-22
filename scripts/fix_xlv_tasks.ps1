# Fix xlv scheduled tasks - use PowerShell to call python with full path
$ErrorActionPreference = "Stop"

$pythonPath = "C:\Program Files\Python313\python.exe"
$scriptPath = "C:\peiwan-site\scripts\xlv_send.py"

$tasks = @(
    @{Name="XlvSendMorning"; Time="08:00"; Style="morning"},
    @{Name="XlvSendNoon";    Time="12:00"; Style="noon"},
    @{Name="XlvSendEvening"; Time="22:00"; Style="evening"}
)

foreach ($t in $tasks) {
    # Remove old task
    Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue

    # Create new task
    $trigger = New-ScheduledTaskTrigger -Daily -At $t.Time
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"& '$pythonPath' '$scriptPath' --style $($t.Style)`"" `
        -WorkingDirectory "C:\peiwan-site\scripts"
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    Register-ScheduledTask `
        -TaskName $t.Name `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -RunLevel Highest

    Write-Host "[OK] $($t.Name) -> $($t.Time) --style $($t.Style)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. All 3 tasks recreated with full python path." -ForegroundColor Cyan
