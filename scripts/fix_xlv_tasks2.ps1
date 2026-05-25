$ErrorActionPreference = "Stop"

$tasks = @(
    @{Name="XlvSendMorning"; Time="08:00"; Style="morning"},
    @{Name="XlvSendNoon";    Time="12:00"; Style="noon"},
    @{Name="XlvSendEvening"; Time="22:00"; Style="evening"}
)

foreach ($t in $tasks) {
    Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue

    $trigger = New-ScheduledTaskTrigger -Daily -At $t.Time
    $action = New-ScheduledTaskAction `
        -Execute "cmd.exe" `
        -Argument "/c C:\peiwan-site\scripts\run_xlv.bat $($t.Style)" `
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

    Write-Host "[OK] $($t.Name) -> $($t.Time) via cmd.exe -> run_xlv.bat $($t.Style)" -ForegroundColor Green
}
