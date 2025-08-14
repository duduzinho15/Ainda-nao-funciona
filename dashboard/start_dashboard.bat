@echo off
chcp 65001 >nul
title Dashboard Garimpeiro Geek

echo.
echo ============================================================
echo 🚀 INICIADOR DO DASHBOARD GARIMPEIRO GEEK
echo ============================================================
echo.

:: Verifica se o ambiente virtual está ativado
if not defined VIRTUAL_ENV (
    echo ⚠️  Ambiente virtual não detectado
    echo 🔧 Ativando ambiente virtual...
    call "..\venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo ❌ Erro ao ativar ambiente virtual
        echo 💡 Execute: ..\venv\Scripts\activate.bat
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual ativado
)

:: Verifica se o Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado no PATH
    echo 💡 Verifique se o Python está instalado
    pause
    exit /b 1
)

:: Verifica se o arquivo run_dashboard.py existe
if not exist "run_dashboard.py" (
    echo ❌ Arquivo run_dashboard.py não encontrado
    pause
    exit /b 1
)

echo.
echo 🎯 Iniciando dashboard com método automático...
echo 💡 Para escolher manualmente, execute: python run_dashboard.py
echo.

:: Executa o dashboard
python run_dashboard.py

:: Se chegou aqui, houve algum erro
if errorlevel 1 (
    echo.
    echo ❌ Erro ao executar dashboard
    echo 💡 Verifique as mensagens de erro acima
    pause
)
