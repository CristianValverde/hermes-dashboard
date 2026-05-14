@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Starting Hermes Analytics Dashboard (Trade Republic Design)...
streamlit run streamlit_app.py --server.port 8501 --server.headless true
pause
