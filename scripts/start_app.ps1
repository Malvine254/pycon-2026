param(
    # Start Mela with the cloud model only, without touching Foundry Local.
    [switch]$SkipLocal
)

Set-Location (Split-Path -Parent $PSScriptRoot)

$appPort = 8000
$portSetting = Select-String -Path .env -Pattern '^\s*APP_PORT\s*=\s*(\d+)' -ErrorAction SilentlyContinue
if ($portSetting) { $appPort = [int]$portSetting.Matches[0].Groups[1].Value }

$localModel = "phi-3.5-mini"
$modelSetting = Select-String -Path .env -Pattern '^\s*LOCAL_MODEL\s*=\s*(\S+)' -ErrorAction SilentlyContinue
if ($modelSetting) { $localModel = $modelSetting.Matches[0].Groups[1].Value }

$connections = Get-NetTCPConnection -LocalPort $appPort -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
    $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    if ($process -and $process.ProcessName -match '^python') {
        Stop-Process -Id $process.Id -Force
        Write-Host "Stopped existing FastAPI process $($process.Id)."
    }
}

$env:PYTHONPATH = "src"
$env:LOCAL_MODEL = $localModel

# The local model is optional: without it Mela runs cloud-only.
if ($SkipLocal) {
    Write-Host "Skipping Foundry Local (-SkipLocal). Starting Mela with the cloud model only." -ForegroundColor Yellow
} elseif (Get-Command foundry -ErrorAction SilentlyContinue) {
    if ((foundry --help 2>&1 | Out-String) -notmatch '\bserver\b') {
        Write-Warning "This Foundry Local version is too old (no 'foundry server' command). Update it: winget upgrade Microsoft.FoundryLocal. Continuing with the cloud model only."
    } else {
        foundry server start
        if ($LASTEXITCODE -eq 0) {
            # Loading downloads Phi on first use (~2.2 GB), so run it in its own window and start Mela now.
            $loadCommand = "foundry model load $localModel; Write-Host ''; Write-Host 'Phi is ready. Mela switches to it within 30 seconds. You can close this window.' -ForegroundColor Green"
            Start-Process powershell -ArgumentList "-NoExit", "-Command", $loadCommand
            Write-Host "Loading $localModel in a separate window (the first time it downloads ~2.2 GB)." -ForegroundColor Cyan
            Write-Host "Mela starts now with the cloud model and switches to Phi automatically once it is loaded." -ForegroundColor Cyan
        } else {
            Write-Warning "Foundry Local server could not start. Continuing with the cloud model only."
        }
    }
} else {
    Write-Warning "Foundry Local is not installed ('foundry' not found). Starting Mela with the cloud model only."
    Write-Host "  To enable the local model: winget install Microsoft.FoundryLocal" -ForegroundColor DarkGray
}

& .\.venv\Scripts\python.exe app\server.py
