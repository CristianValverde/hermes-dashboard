Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  HERMES FALLBACK TEST - Desde Windows" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Get WSL2 IP
Write-Host "[1/4] Detectando IP de WSL2..." -ForegroundColor Yellow
$wslIp = (wsl hostname -I).Split(" ")[0]
Write-Host "     WSL2 IP: $wslIp" -ForegroundColor White

# 2. Test Ollama API (simple GET)
Write-Host "`n[2/4] Probando conexión a Ollama (GET)..." -ForegroundColor Yellow
try {
    $result = curl.exe -s -o NUL -w "%{http_code}" "http://${wslIp}:11434/api/tags" 2>$null
    if ($result -eq "200") {
        Write-Host "     ✅ HTTP $result - Ollama responde!" -ForegroundColor Green
    } else {
        Write-Host "     ❌ HTTP $result - No se puede conectar" -ForegroundColor Red
    }
} catch {
    Write-Host "     ❌ Error: $_" -ForegroundColor Red
}

# 3. Test model inference (POST)
Write-Host "`n[3/4] Probando inferencia del modelo..." -ForegroundColor Yellow
try {
    $json = '{"model":"qwen3.5:9b","messages":[{"role":"user","content":"Say only: OK"}],"max_tokens":5}'
    $result = curl.exe -s -w "`n%{http_code}" -X POST "http://${wslIp}:11434/v1/chat/completions" `
        -H "Content-Type: application/json" -d $json 2>$null
    $lines = $result -split "`n"
    $code = $lines[-1].Trim()
    if ($code -eq "200") {
        Write-Host "     ✅ HTTP $code - Modelo responde correctamente!" -ForegroundColor Green
        try { Write-Host "     Respuesta: $($lines[0][0..80] -join '')" -ForegroundColor White } catch {}
    } else {
        Write-Host "     ❌ HTTP $code - Error de inferencia" -ForegroundColor Red
    }
} catch {
    Write-Host "     ❌ Error: $_" -ForegroundColor Red
}

# 4. Verify config
Write-Host "`n[4/4] Verificando config de Hermes..." -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\AppData\Local\hermes\config.yaml"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw
    if ($config -match "192.168.1.31") {
        Write-Host "     ✅ Config apunta a WSL2 IP (192.168.1.31)" -ForegroundColor Green
    } elseif ($config -match "127.0.0.1") {
        Write-Host "     ⚠️ Config usa localhost - puede fallar POST" -ForegroundColor Yellow
    }
    if ($config -match "fallback_providers.*Ollama Qwen3.5") {
        Write-Host "     ✅ fallback_providers configurado" -ForegroundColor Green
    }
    if ($config -match "fallback_model:") {
        Write-Host "     ✅ fallback_model section activa" -ForegroundColor Green
    }
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  RESULTADO:" -ForegroundColor Cyan
Write-Host "  Si los tests 2 y 3 pasan, el fallback funcionará." -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
