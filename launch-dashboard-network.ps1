# Hermes Dashboard Network Launcher for PowerShell
$ErrorActionPreference = "Stop"

$dashboardDir = Join-Path $PSScriptRoot "api"
$venvPython = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "[Hermes Dashboard] Using Hermes venv Python" -ForegroundColor Green
    $python = $venvPython
} else {
    Write-Host "[Hermes Dashboard] Using system Python" -ForegroundColor Yellow
    $python = "python"
}

try {
    & $python -c "import flask" 2>$null
} catch {
    Write-Host "[!] Flask not found. Installing..." -ForegroundColor Yellow
    & $python -m pip install flask pandas
}

$env:HERMES_DASHBOARD_ACCESS_MODE = "network"
$env:HERMES_DASHBOARD_HOST = "0.0.0.0"
$env:HERMES_DASHBOARD_PORT = "8590"

Write-Host "[Hermes Dashboard] Starting in network mode" -ForegroundColor Cyan
Write-Host "[Hermes Dashboard] Local URL:   http://localhost:8590" -ForegroundColor Cyan
Write-Host "[Hermes Dashboard] Remote URL:  use your LAN IP or VPN IP on port 8590" -ForegroundColor Yellow
Write-Host "[Hermes Dashboard] Best for trusted LAN or mesh VPNs such as Tailscale, ZeroTier, WireGuard, or OpenVPN" -ForegroundColor Yellow

$ipv4Addresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' } |
    Select-Object -ExpandProperty IPAddress -Unique

if ($ipv4Addresses) {
    Write-Host "[Hermes Dashboard] Candidate IPv4 addresses:" -ForegroundColor Green
    foreach ($ip in $ipv4Addresses) {
        Write-Host "  - http://$ip`:8590" -ForegroundColor Green
    }
}

Start-Process "http://localhost:8590"
Set-Location $dashboardDir
& $python flask_app.py
