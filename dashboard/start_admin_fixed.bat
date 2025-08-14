@echo off
chcp 65001 >nul
title Dashboard Garimpeiro Geek - Administrador

echo.
echo ============================================================
echo 🚀 INICIADOR DO DASHBOARD GARIMPEIRO GEEK - CORRIGIDO
echo ============================================================
echo.

:: Verifica se é administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Executando como administrador
) else (
    echo ⚠️ Não é administrador
    echo 🔧 Tentando elevar privilégios...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && \"%~f0\"' -Verb RunAs"
    exit /b
)

:: Define o diretório do projeto
set PROJECT_DIR=%~dp0..
echo 🔍 Diretório do projeto: %PROJECT_DIR%

:: Verifica se o ambiente virtual existe
if exist "%PROJECT_DIR%\venv\Scripts\activate.bat" (
    echo 🔧 Ativando ambiente virtual...
    call "%PROJECT_DIR%\venv\Scripts\activate.bat"
    echo ✅ Ambiente virtual ativado
) else (
    echo ❌ Ambiente virtual não encontrado em: %PROJECT_DIR%\venv\Scripts\activate.bat
    echo 💡 Verifique se o ambiente virtual foi criado corretamente
    pause
    exit /b 1
)

:: Cria exceção no firewall primeiro
echo 🔧 Criando exceção no firewall...
netsh advfirewall firewall add rule name="Dashboard Garimpeiro Geek" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Exceção no firewall criada com sucesso!
) else (
    echo ⚠️ Erro ao criar exceção no firewall (pode já existir)
)

:: Cria exceção para porta 3000 também
echo 🔧 Criando exceção para porta 3000...
netsh advfirewall firewall add rule name="Dashboard Garimpeiro Geek Porta 3000" dir=in action=allow protocol=TCP localport=3000 >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Exceção para porta 3000 criada!
) else (
    echo ⚠️ Erro ao criar exceção para porta 3000 (pode já existir)
)

:: Inicia o dashboard
echo 🚀 Iniciando dashboard...
cd /d "%~dp0"

:: Tenta iniciar com Flask primeiro
echo 🔄 Tentando Flask na porta 8080...
python -c "from app import app; print('✅ Dashboard iniciado com sucesso!'); print('🌐 Acesse: http://127.0.0.1:8080'); app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)"

pause
