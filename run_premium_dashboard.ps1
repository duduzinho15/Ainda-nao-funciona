param(
    [string]$ProjectDir = "$PWD",
    [string]$PythonExe = ".\.venv\Scripts\python.exe",
    [ValidateSet("0","1")] [string]$Dark = "1"
)

$ErrorActionPreference = "Stop"
Push-Location $ProjectDir

if (!(Test-Path $PythonExe)) {
    Write-Host "Atenção: venv não encontrado em .\.venv. Ajuste -PythonExe ou crie o venv." -ForegroundColor Yellow
    exit 1
}

$env:DARK = $Dark
Write-Host "Iniciando Premium Dashboard em modo desktop..." -ForegroundColor Green
if ($Dark -eq '1') {
    Write-Host "Tema: ESCURO" -ForegroundColor Cyan
} else {
    Write-Host "Tema: CLARO" -ForegroundColor Cyan
}

& $PythonExe -m flet_app.premium_dashboard --desktop

Pop-Location
