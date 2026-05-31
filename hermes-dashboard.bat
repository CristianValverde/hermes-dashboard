@echo off
cd /d "C:\Users\Cristian Valverde\hermes-dashboard\api"

REM Try Hermes venv Python first (has Flask)
set PYTHON=C:\Users\Cristian Valverde\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe
if exist "%PYTHON%" (
    start "" "http://localhost:8590"
    "%PYTHON%" flask_app.py
    goto :eof
)

REM Fallback to system Python
start "" "http://localhost:8590"
python flask_app.py
