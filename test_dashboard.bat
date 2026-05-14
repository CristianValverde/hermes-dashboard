@echo off
echo 🔧 Ejecutando test del dashboard...
cd /d "%~dp0"
python test_dashboard.py
echo.
echo Si ves errores, ejecuta install_deps.bat primero
pause
