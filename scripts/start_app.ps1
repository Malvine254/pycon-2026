Set-Location (Split-Path -Parent $PSScriptRoot)

$appPort = 8000
$portSetting = Select-String -Path .env -Pattern '^\s*APP_PORT\s*=\s*(\d+)' -ErrorAction SilentlyContinue
if ($portSetting) { $appPort = [int]$portSetting.Matches[0].Groups[1].Value }

$connections = Get-NetTCPConnection -LocalPort $appPort -State Listen -ErrorAction SilentlyContinue
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

# The local model is optional: without it Mela runs cloud-only.
if (Get-Command foundry -ErrorAction SilentlyContinue) {
    if ((foundry --help 2>&1 | Out-String) -notmatch '\bserver\b') {
        Write-Warning "This Foundry Local version is too old (no 'foundry server' command). Update it: winget upgrade Microsoft.FoundryLocal. Continuing with the cloud model only."
    } else {
        foundry server start
        if ($LASTEXITCODE -eq 0) {
            foundry model load $env:LOCAL_MODEL
            if ($LASTEXITCODE -ne 0) { Write-Warning "Could not load $($env:LOCAL_MODEL). Continuing with the cloud model only." }
            foundry server status
        } else {
            Write-Warning "Foundry Local server could not start. Continuing with the cloud model only."
        }
    }
} else {
    Write-Warning "Foundry Local is not installed ('foundry' not found). Starting Mela with the cloud model only."
    Write-Host "  To enable the local model: winget install Microsoft.FoundryLocal" -ForegroundColor DarkGray
}

& .\.venv\Scripts\python.exe app\server.py
