@echo off
echo 🔧 Instalando dependencias para Hermes Dashboard...
echo 📦 Esto puede tomar unos minutos...

REM Usar Python 3.13.13 si está disponible
where python3.13.exe >nul 2>nul
if %errorlevel% equ 0 (
    echo Usando Python 3.13.13...
    python3.13 -m pip install --upgrade pip
    python3.13 -m pip install streamlit pandas plotly sqlalchemy
    goto :ready
)

REM Usar Python 3.14 (el que usa el .bat actual)
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo Usando Python (default)...
    python -m pip install --upgrade pip
    python -m pip install streamlit pandas plotly sqlalchemy
    goto :ready
)

echo ❌ No se encontró Python instalado
pause
exit /b 1

:ready
echo ✅ Dependencias instaladas correctamente
echo 🚀 Ahora puedes ejecutar launch_dashboard_now.bat
pause
