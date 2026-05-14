# PowerShell script para lanzar Hermes Dashboard
Set-Location "C:\Users\Cristian Valverde\hermes-dashboard"
Write-Host "🚀 Iniciando Hermes Dashboard..." -ForegroundColor Green
Write-Host "📊 Streamlit se abrirá en http://localhost:8501" -ForegroundColor Cyan
Write-Host "⚠️  Mantén esta ventana abierta" -ForegroundColor Yellow

python -m streamlit run streamlit_app.py

Write-Host "`n✅ Dashboard detenido" -ForegroundColor Green
Pause
