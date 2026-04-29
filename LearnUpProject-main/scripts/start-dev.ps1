# Start LearnUp backend + frontend and verify they talk to each other.
# Run from PowerShell:  .\scripts\start-dev.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "Stopping anything on ports 8000 and 5173..."
foreach ($port in 8000, 5173) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 1

Write-Host "Starting FastAPI on http://127.0.0.1:8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location `"$Backend`"; `$env:PYTHONPATH=`"$Backend`"; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
) | Out-Null

Start-Sleep -Seconds 4

Write-Host "Starting Vite on http://localhost:5173 (VITE_API_URL -> http://127.0.0.1:8000) ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location `"$Frontend`"; `$env:VITE_API_URL='http://127.0.0.1:8000'; npm run dev"
) | Out-Null

Start-Sleep -Seconds 8

Write-Host "`nHealth checks:"
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing -TimeoutSec 15
    Write-Host "  Backend /  -> $($r.StatusCode) $($r.Content)"
} catch {
    Write-Host "  Backend /  -> FAILED: $($_.Exception.Message)"
}

try {
    $o = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/openapi.json" -UseBasicParsing -TimeoutSec 15).Content
    if ($o -match '"/auth/login"') {
        Write-Host "  OpenAPI    -> /auth/login present (login route OK)"
    } else {
        Write-Host "  OpenAPI    -> WARNING: /auth/login not found (wrong app on 8000?)"
    }
} catch {
    Write-Host "  OpenAPI    -> FAILED: $($_.Exception.Message)"
}

try {
    $h = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 15).Content | ConvertFrom-Json
    if ($h.student_card_api -eq "v2-ensure-row") {
        Write-Host "  /health    -> LearnUp v2 student card API OK"
    } else {
        Write-Host "  /health    -> WARNING: unexpected payload (wrong app on 8000?)"
    }
} catch {
    Write-Host "  /health    -> FAILED: $($_.Exception.Message)"
}

try {
    $f = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 15
    Write-Host "  Frontend   -> $($f.StatusCode) OK"
} catch {
    Write-Host "  Frontend   -> FAILED: $($_.Exception.Message)"
}

Write-Host "`nOpen: http://localhost:5173"
Write-Host "API docs: http://127.0.0.1:8000/docs"
Write-Host "(Two new PowerShell windows were opened for backend and frontend.)"
