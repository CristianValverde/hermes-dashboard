@echo off
title Hermes Dashboard v6 - React+Flask

echo ============================================
echo   HERMES DASHBOARD v6
echo   React + Flask
echo ============================================
echo.

cd /d "%~dp0api"

echo [1/2] Verificando dependencias...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [!] Instalando Flask...
    pip install flask
)

echo [2/2] Iniciando servidor...
echo.
echo   Dashboard: http://localhost:8502
echo   Cerrar:    Ctrl+C en esta ventana
echo.
echo ============================================
python flask_app.py

echo.
echo Servidor detenido.
pause
