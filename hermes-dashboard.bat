@echo off
cd /d "%~dp0api"
set HERMES_DASHBOARD_ACCESS_MODE=localhost
set HERMES_DASHBOARD_HOST=127.0.0.1
set HERMES_DASHBOARD_PORT=8590

REM Try Hermes venv Python first (has Flask)
set PYTHON=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe
if exist "%PYTHON%" (
    echo [Hermes Dashboard] Starting in localhost-only mode on http://localhost:8590
    start "" "http://localhost:8590"
    "%PYTHON%" flask_app.py
    goto :eof
)

REM Fallback to system Python
echo [Hermes Dashboard] Starting in localhost-only mode on http://localhost:8590
start "" "http://localhost:8590"
python flask_app.py
