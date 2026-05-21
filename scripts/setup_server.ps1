# peiwan.co server setup script
# Run once on Windows server as administrator
# Usage: .\scripts\setup_server.ps1 -ApiKey "your-key" -RepoUrl "https://github.com/..."

param(
    [string]$ApiKey,
    [string]$ApiBase = "https://token-plan-cn.xiaomimimo.com/anthropic",
    [string]$Model = "mimo-v2-flash",
    [string]$RepoUrl = ""
)

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "peiwan.co Server Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check dependencies
Write-Host "[1/6] Checking dependencies..." -ForegroundColor Yellow

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "  [!] Python not installed" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Python" -ForegroundColor Green

Write-Host "  Installing anthropic package..." -ForegroundColor Gray
$pipResult = python -m pip install anthropic --quiet 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] pip install returned exit code $LASTEXITCODE" -ForegroundColor Yellow
    Write-Host "  Output: $pipResult" -ForegroundColor Gray
} else {
    Write-Host "  [OK] anthropic" -ForegroundColor Green
}

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "  [!] Git not installed" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Git" -ForegroundColor Green

$hugo = Get-Command hugo -ErrorAction SilentlyContinue
if (-not $hugo) {
    Write-Host "  Installing Hugo..." -ForegroundColor Gray
    $hasWinget = Get-Command winget -ErrorAction SilentlyContinue
    if ($hasWinget) {
        winget install Hugo.Hugo.Extended --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "  [!] Cannot auto-install Hugo" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  [OK] Hugo" -ForegroundColor Green

# Step 2: Configure API key
Write-Host ""
Write-Host "[2/6] Configuring API key..." -ForegroundColor Yellow

if (-not $ApiKey) {
    $ApiKey = Read-Host "  Enter MiMo API Key"
}

[System.Environment]::SetEnvironmentVariable("MIMO_API_KEY", $ApiKey, "User")
[System.Environment]::SetEnvironmentVariable("MIMO_API_BASE", $ApiBase, "User")
[System.Environment]::SetEnvironmentVariable("MIMO_MODEL", $Model, "User")

$env:MIMO_API_KEY = $ApiKey
$env:MIMO_API_BASE = $ApiBase
$env:MIMO_MODEL = $Model

Write-Host "  [OK] Environment variables saved" -ForegroundColor Green

# Step 3: Git config
Write-Host ""
Write-Host "[3/6] Configuring Git..." -ForegroundColor Yellow

$repoDir = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$repoDir\.git")) {
    Write-Host "  Initializing git repo..." -ForegroundColor Gray
    git init $repoDir
    git -C $repoDir add .
    git -C $repoDir commit -m "feat: init peiwan.co site"
}

if ($RepoUrl) {
    $remotes = git -C $repoDir remote
    if (-not $remotes) {
        git -C $repoDir remote add origin $RepoUrl
        Write-Host "  [OK] Remote added" -ForegroundColor Green
    }
    git -C $repoDir branch -M main
    git -C $repoDir push -u origin main
    Write-Host "  [OK] Pushed to GitHub" -ForegroundColor Green
} else {
    Write-Host "  [i] No remote URL provided" -ForegroundColor Yellow
}

# Step 4: Install PaperMod theme
Write-Host ""
Write-Host "[4/6] Installing Hugo theme..." -ForegroundColor Yellow

$themeDir = "$repoDir\site\themes\PaperMod"
if (-not (Test-Path $themeDir)) {
    git submodule add --depth=1 https://github.com/adityatelange/hugo-PaperMod.git $themeDir 2>$null
    if (-not $?) {
        git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git $themeDir 2>$null
    }
    Write-Host "  [OK] PaperMod installed" -ForegroundColor Green
} else {
    Write-Host "  [OK] PaperMod exists" -ForegroundColor Green
}

# Step 5: Test Hugo build
Write-Host ""
Write-Host "[5/6] Testing Hugo build..." -ForegroundColor Yellow

hugo -s "$repoDir\site" --minify --quiet
if ($?) {
    Write-Host "  [OK] Hugo build success" -ForegroundColor Green
} else {
    Write-Host "  [!] Hugo build failed" -ForegroundColor Red
}

# Step 6: Test content generation
Write-Host ""
Write-Host "[6/6] Testing content generation (1 article)..." -ForegroundColor Yellow

python "$repoDir\scripts\generate.py" --limit 1
if ($?) {
    Write-Host "  [OK] Content generation works" -ForegroundColor Green
} else {
    Write-Host "  [!] Content generation failed" -ForegroundColor Red
}

# Done
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Install scheduled task: .\scripts\install_task.ps1" -ForegroundColor Gray
Write-Host "  2. Connect Cloudflare Pages" -ForegroundColor Gray
Write-Host "  3. Apply for Google AdSense" -ForegroundColor Gray
Write-Host ""
