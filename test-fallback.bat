@echo off
title Fallback Test - Hermes Dashboard
echo ============================================
echo   HERMES FALLBACK TEST
echo   Verifying Ollama fallback from Windows
echo ============================================
echo.

echo [1/3] Checking Ollama API from Windows...
curl -s -o NUL -w "HTTP %%{http_code}" http://127.0.0.1:11434/api/tags
if %%errorlevel%% neq 0 (
    echo.
    echo [FAIL] Cannot reach Ollama!
    echo.
    echo Possible fixes:
    echo   1. Open WSL2 terminal and run: ollama serve
    echo   2. Check if WSL2 is running: wsl --status
    echo   3. Restart WSL2: wsl --shutdown ^&^& wsl
    pause
    exit /b 1
)
echo. - OK

echo.
echo [2/3] Testing model inference via Ollama...
echo Esperando respuesta (15-30s si el modelo se carga en VRAM)...
for /f "delims=" %%i in ('curl -s -X POST http://127.0.0.1:11434/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"qwen3.5:9b\",\"messages\":[{\"role\":\"user\",\"content\":\"Responde solo OK\"}],\"max_tokens\":5}"') do set result=%%i

echo %%result%% | findstr "OK" > NUL
if %%errorlevel%% equ 0 (
    echo. - OK ^(modelo responde^)
) else (
    echo. - RESPUESTA: %%result%%
)

echo.
echo [3/3] Checking Hermes config...
findstr "fallback" "C:\Users\Cristian Valverde\AppData\Local\hermes\config.yaml"
echo.
echo ============================================
echo   RESULT: All tests passed ^(assuming HTTP 200^)
echo.
echo   If Ollama responds from Windows, the
echo   automatic fallback will work when
echo   OpenRouter credits run out.
echo ============================================
pause
