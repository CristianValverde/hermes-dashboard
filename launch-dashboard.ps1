# Hermes Dashboard Launcher for PowerShell
$ErrorActionPreference = "Stop"

$dashboardDir = Join-Path $PSScriptRoot "api"
$venvPython = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"

# Try Hermes venv first
if (Test-Path $venvPython) {
    Write-Host "[Hermes Dashboard] Using Hermes venv Python" -ForegroundColor Green
    $python = $venvPython
} else {
    Write-Host "[Hermes Dashboard] Using system Python" -ForegroundColor Yellow
    $python = "python"
}

# Verify Flask is available
try {
    & $python -c "import flask" 2>$null
} catch {
    Write-Host "[!] Flask not found. Installing..." -ForegroundColor Yellow
    & $python -m pip install flask pandas
}

$env:HERMES_DASHBOARD_ACCESS_MODE = "localhost"
$env:HERMES_DASHBOARD_HOST = "127.0.0.1"
$env:HERMES_DASHBOARD_PORT = "8590"

Write-Host "[Hermes Dashboard] Starting in localhost-only mode on http://localhost:8590" -ForegroundColor Cyan
Start-Process "http://localhost:8590"
Set-Location $dashboardDir
& $python flask_app.py
