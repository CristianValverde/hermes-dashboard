@echo off

chcp 65001 >nul

title Hermes Fallback Test

cls

echo ============================================

echo   HERMES FALLBACK TEST

echo ============================================

echo.



echo [1/3] Detectando IP de WSL2...

for /f %%i in ('wsl hostname -I') do set WSL_IP=%%i

echo     WSL2 IP: %WSL_IP%

echo.



echo [2/3] Probando conexion a Ollama...

curl.exe -s -o NUL -w "     HTTP: %%{http_code}

" http://%WSL_IP%:11434/api/tags

if errorlevel 1 (

    echo     ERROR: No se puede conectar a Ollama

    echo.

    echo     Posibles causas:

    echo     1. Ollama no esta corriendo en WSL2

    echo     2. La IP de WSL2 cambio

    echo     3. Firewall bloqueando

    echo.

    echo     Para verificar: wsl curl -s http://127.0.0.1:11434/api/tags

    pause

    exit /b 1

)

echo.



echo [3/3] Probando inferencia del modelo (POST)...

echo     Esto puede tomar 30-60s si el modelo carga en VRAM...

curl.exe -s -X POST http://%WSL_IP%:11434/v1/chat/completions ^

  -H "Content-Type: application/json" ^

  -d "{"model":"qwen3.5:9b","messages":[{"role":"user","content":"Say OK in one word"}],"max_tokens":10}"

echo.

echo.

echo ============================================

echo   Prueba completada. Si ves HTTP 200 y una

echo   respuesta del modelo, el fallback funciona.

echo ============================================

pause

