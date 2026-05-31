@echo off
title Hermes Dashboard - React+Flask
cd /d "%~dp0api"

REM Try Hermes venv Python first
set VENV_PY=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe
if exist "%VENV_PY%" (
    echo [Hermes Dashboard] Using Hermes venv Python
    start "" "http://localhost:8590"
    "%VENV_PY%" flask_app.py
    goto :eof
)

REM Fallback
echo [Hermes Dashboard] Using system Python
start "" "http://localhost:8590"
python flask_app.py
pause
