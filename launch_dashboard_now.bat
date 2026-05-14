@echo off
echo 🔧 Verificando dependencias...

REM Verificar si streamlit está instalado
python -c "import streamlit" >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Streamlit no está instalado
    echo 📦 Instalando dependencias... Esto puede tomar unos minutos...
    python -m pip install --upgrade pip
    python -m pip install streamlit pandas plotly sqlalchemy
    echo ✅ Dependencias instaladas
) else (
    echo ✅ Streamlit ya está instalado
)

echo.
echo 🔧 Cambiando al directorio del dashboard
cd /d "C:\Users\Cristian Valverde\hermes-dashboard"

echo 🚀 Iniciando Hermes Dashboard...
echo 📊 Streamlit se abrirá en http://localhost:8501
echo ⚠️  Mantén esta ventana abierta

python -m streamlit run streamlit_app.py

echo.
echo ✅ Dashboard detenido
pause
