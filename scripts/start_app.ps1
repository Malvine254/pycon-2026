Set-Location (Split-Path -Parent $PSScriptRoot)

$connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
    $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    if ($process -and $process.ProcessName -match '^python') {
        Stop-Process -Id $process.Id -Force
        Write-Host "Stopped existing FastAPI process $($process.Id)."
    }
}

$env:PYTHONPATH = "src"
$env:LOCAL_RUNTIME = "foundry-local"
$env:LOCAL_MODEL = "phi-3.5-mini"

foundry server start
if ($LASTEXITCODE -ne 0) { throw "Foundry Local server could not start." }
foundry model load phi-3.5-mini
if ($LASTEXITCODE -ne 0) { throw "Phi could not be loaded." }

& .\.venv\Scripts\python.exe app\server.py
