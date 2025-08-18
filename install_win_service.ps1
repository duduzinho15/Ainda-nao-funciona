# install_win_service.ps1
param(
  [string]$ProjectDir = "$PWD",
  [string]$PythonExe  = "C:\Python311\python.exe",
  [string]$NssmExe    = "C:\tools\nssm\nssm.exe",
  [string]$ServiceName = "GarimpeiroGeek"
)
$ErrorActionPreference = "Stop"
Push-Location $ProjectDir

$venv = Join-Path $ProjectDir ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
if (!(Test-Path $venvPython)) { & $PythonExe -m venv $venv }
& $venvPython -m pip install --upgrade pip
if (Test-Path (Join-Path $ProjectDir "requirements.txt")) {
  & $venvPython -m pip install -r requirements.txt
}
& $venvPython -m playwright install chromium

$logsDir = Join-Path $ProjectDir "logs"
if (!(Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }

# Recria serviço
& $NssmExe stop $ServiceName 2>$null
& $NssmExe remove $ServiceName confirm 2>$null

# Instala supervisor
& $NssmExe install $ServiceName $venvPython (Join-Path $ProjectDir "supervisor_service.py")
& $NssmExe set $ServiceName AppDirectory $ProjectDir
& $NssmExe set $ServiceName AppStdout (Join-Path $logsDir "service.out.log")
& $NssmExe set $ServiceName AppStderr (Join-Path $logsDir "service.err.log")
& $NssmExe set $ServiceName AppRotateFiles 1
& $NssmExe set $ServiceName AppRotateOnline 1
& $NssmExe set $ServiceName AppRotateBytes 10485760
& $NssmExe set $ServiceName Start SERVICE_AUTO_START

# Variáveis de ambiente úteis para o serviço
& $NssmExe set $ServiceName AppEnvironmentExtra `
"PYTHONUTF8=1" `
"PYTHONIOENCODING=UTF-8" `
"DASHBOARD_ENABLED=1" `
"DASHBOARD_HEADLESS=1" `
"DASHBOARD_HOST=127.0.0.1" `
"DASHBOARD_PORT=8550"

sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/5000/restart/5000 | Out-Null
& $NssmExe start $ServiceName
Pop-Location
Write-Host "Servico $ServiceName instalado e iniciado."
