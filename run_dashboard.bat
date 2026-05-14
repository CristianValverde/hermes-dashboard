@echo off
echo Starting Hermes Dashboard...
echo.
echo Opening: http://localhost:8501
echo.

cd /d "C:\Users\Cristian Valverde\hermes-dashboard"

if not exist streamlit_app.py (
    echo ERROR: streamlit_app.py not found
    pause
    exit /b 1
)

echo Running: python -m streamlit run streamlit_app.py
echo.

python -m streamlit run streamlit_app.py --server.port 8501

echo.
echo Dashboard stopped.
pause
