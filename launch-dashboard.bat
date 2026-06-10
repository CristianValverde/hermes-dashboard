@echo off
title Hermes Dashboard - React+Flask
cd /d "%~dp0api"

REM Try Hermes venv Python first
set VENV_PY=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe
set HERMES_DASHBOARD_ACCESS_MODE=localhost
set HERMES_DASHBOARD_HOST=127.0.0.1
set HERMES_DASHBOARD_PORT=8590
if exist "%VENV_PY%" (
    echo [Hermes Dashboard] Using Hermes venv Python
    echo [Hermes Dashboard] Starting in localhost-only mode on http://localhost:8590
    start "" "http://localhost:8590"
    "%VENV_PY%" flask_app.py
    goto :eof
)

REM Fallback
echo [Hermes Dashboard] Using system Python
echo [Hermes Dashboard] Starting in localhost-only mode on http://localhost:8590
start "" "http://localhost:8590"
python flask_app.py
pause
