# run_both_dev.ps1
param(
  [string]$ProjectDir = "$PWD",
  [string]$PythonExe  = "python"
)
$ErrorActionPreference = "Stop"
Push-Location $ProjectDir

# Mata processo que segura a porta 8550
try {
  $conns = Get-NetTCPConnection -LocalPort 8550 -ErrorAction SilentlyContinue
  if ($conns) { $conns | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }
} catch { 
  netstat -ano | findstr ":8550" | ForEach-Object { $_.Split()[4] } | ForEach-Object { taskkill /PID $_ /F } 
}

$venv = Join-Path $ProjectDir ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
if (!(Test-Path $venvPython)) { & $PythonExe -m venv $venv }
& $venvPython -m pip install --upgrade pip
if (Test-Path (Join-Path $ProjectDir "requirements.txt")) {
  & $venvPython -m pip install -r requirements.txt
}
& $venvPython -m playwright install chromium

$env:DRY_RUN = "1"
$env:DASHBOARD_ENABLED = "1"
$env:DASHBOARD_HEADLESS = "1"
$env:DARK = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "UTF-8"
& $venvPython (Join-Path $ProjectDir "supervisor_service.py")

Pop-Location
