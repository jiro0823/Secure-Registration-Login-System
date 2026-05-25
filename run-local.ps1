param(
    [int]$PreferredPort = 8000
)

$ErrorActionPreference = "Stop"

function Test-PortInUse {
    param([int]$Port)
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $listener
}

$port = $PreferredPort
while (Test-PortInUse -Port $port) {
    $port++
}

$backendPath = Join-Path $PSScriptRoot "backend"
$venvPython = Join-Path $backendPath "venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

Write-Host "Starting Secure Auth System on http://localhost:$port"
Write-Host "Using MySQL from backend/.env DATABASE_URL"

Push-Location $backendPath
try {
    & $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
} finally {
    Pop-Location
}
