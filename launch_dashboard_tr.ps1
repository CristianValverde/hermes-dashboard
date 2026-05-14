# PowerShell script to launch Hermes Analytics Dashboard
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

& .venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Hermes Analytics Dashboard (Trade Republic Design)..." -ForegroundColor Green
streamlit run streamlit_app.py --server.port 8501 --server.headless true
