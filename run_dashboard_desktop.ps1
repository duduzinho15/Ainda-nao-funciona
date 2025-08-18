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
& $PythonExe -m flet_app.main --desktop

Pop-Location
