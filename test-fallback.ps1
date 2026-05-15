$host.ui.RawUI.WindowTitle = "Hermes Fallback Test"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  HERMES FALLBACK TEST" -ForegroundColor Cyan
Write-Host "  Verificando Ollama local desde Windows" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get WSL2 IP
Write-Host "[1/3] Detectando IP de WSL2..." -ForegroundColor Yellow
$wslIp = (wsl.exe hostname -I 2>$null).Split(" ")[0]
if (-not $wslIp) {
    Write-Host "     ERROR: No se pudo obtener IP de WSL2" -ForegroundColor Red
    Write-Host "     Asegurate que WSL2 esta corriendo: wsl --status" -ForegroundColor Yellow
    exit 1
}
Write-Host "     WSL2 IP: $wslIp" -ForegroundColor White

# Step 2: Test GET
Write-Host ""
Write-Host "[2/3] Probando conexion a Ollama..." -ForegroundColor Yellow
try {
    $url = "http://${wslIp}:11434/api/tags"
    $response = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "     CONEXION: OK (GET HTTP 200)" -ForegroundColor Green
    } else {
        Write-Host "     CONEXION: Fallo (HTTP $($response.StatusCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host "     CONEXION: Fallo - $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Posibles causas:"
    Write-Host "  1. Ollama no esta corriendo en WSL2"
    Write-Host "  2. La IP de WSL2 cambio (puede diferir de 192.168.1.31)"
    Write-Host "  3. Firewall bloqueando el puerto 11434"
    Write-Host ""
    Write-Host "Para verificar:"
    Write-Host "  wsl curl -s http://127.0.0.1:11434/api/tags"
    exit 1
}

# Step 3: Test POST (chat completion)
Write-Host ""
Write-Host "[3/3] Probando inferencia del modelo (POST)..." -ForegroundColor Yellow
try {
    $body = '{"model":"qwen3.5:9b","messages":[{"role":"user","content":"Say only OK in one word"}],"max_tokens":10}'
    $url = "http://${wslIp}:11434/v1/chat/completions"
    $response = Invoke-WebRequest -Uri $url -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 60
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        $model = $data.model
        $reply = $data.choices[0].message.content
        Write-Host "     MODELO: $model" -ForegroundColor Green
        Write-Host "     RESPUESTA: '$reply'" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Green
        Write-Host "  FALLBACK FUNCIONAL!" -ForegroundColor Green
        Write-Host "  qwen3.5:9b responde desde Windows" -ForegroundColor Green
        Write-Host "  Hermes Agent puede usarlo como fallback" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green
    } else {
        Write-Host "     INFERENCIA: Fallo (HTTP $($response.StatusCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host "     INFERENCIA: Fallo - $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Posibles causas:"
    Write-Host "  1. El modelo qwen3.5:9b no esta descargado"
    Write-Host "  2. Tiempo de espera insuficiente (60s)"
    Write-Host "  3. La IP de WSL2 cambio"
    Write-Host ""
    Write-Host "Para verificar desde WSL2:"
    Write-Host "  wsl curl -s http://127.0.0.1:11434/api/tags"
}

pause
