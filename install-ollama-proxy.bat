@echo off
title Hermes — Port Proxy Ollama
cd /d "%~dp0"

REM Check if already admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ============================================
    echo   INSTALANDO PORTPROXY PARA OLLAMA
    echo ============================================
    echo.
    echo Se requieren permisos de administrador.
    echo Solicitud en 3 segundos...
    echo.
    timeout /t 3 /nobreak >nul
    
    REM Re-lanzar como administrador via PowerShell
    powershell -Command "Start-Process cmd -ArgumentList '/c ""%~f0""' -Verb RunAs"
    exit /b
)

:ADMIN
echo ============================================
echo   INSTALANDO PORTPROXY PARA OLLAMA
echo ============================================
echo.
echo Creando proxy: 127.0.0.1:11434 → 192.168.1.31:11434
echo.

netsh interface portproxy add v4tov4 ^
  listenaddress=127.0.0.1 listenport=11434 ^
  connectaddress=192.168.1.31 connectport=11434

if %errorlevel% == 0 (
    echo.
    echo ✅ PROXY INSTALADO. Ollama ya es accesible desde Windows.
    echo.
    netsh interface portproxy show all
) else (
    echo.
    echo ❌ Error creando proxy (puede que ya exista)
    echo    Verifica con: netsh interface portproxy show all
)

echo.
echo ============================================
echo   Verificando conexion...
echo ============================================
echo.
echo Probando GET...
curl -s -o NUL -w "HTTP: %%{http_code}
" http://127.0.0.1:11434/api/tags
echo.
echo Probando POST...
curl -s -X POST http://127.0.0.1:11434/v1/chat/completions -H "Content-Type: application/json" -d "{"model":"qwen3.5:9b","messages":[{"role":"user","content":"Say only OK"}],"max_tokens":10}"
echo.
echo ============================================
echo   LISTO! Si ves HTTP 200 arriba, el fallback
echo   a Ollama ya funciona desde Windows.
echo ============================================
pause
