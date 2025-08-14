@echo off
chcp 65001 >nul
title Dashboard Garimpeiro Geek - Administrador

echo.
echo ============================================================
echo 🚀 INICIADOR DO DASHBOARD GARIMPEIRO GEEK
echo ============================================================
echo.

:: Verifica se é administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Executando como administrador
) else (
    echo ⚠️ Não é administrador
    echo 🔧 Tentando elevar privilégios...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d "%~dp0" && "%~f0"' -Verb RunAs"
    exit /b
)

:: Ativa ambiente virtual
if not defined VIRTUAL_ENV (
    echo 🔧 Ativando ambiente virtual...
    call "..\venv\Scripts\activate.bat"
)

:: Inicia o dashboard
echo 🚀 Iniciando dashboard...
cd /d "%~dp0"
python start_windows_final.py

pause
